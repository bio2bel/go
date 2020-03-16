# -*- coding: utf-8 -*-

"""Manager for Bio2BEL GO."""

import logging
from collections import defaultdict
from typing import Iterable, List, Mapping, Optional, Set, Tuple

import networkx as nx
import pandas as pd
import time
from protmapper.api import hgnc_name_to_id
from protmapper.uniprot_client import get_gene_name
from sqlalchemy.ext.declarative import DeclarativeMeta
from tqdm import tqdm

import pybel.dsl
from bio2bel.manager.compath import CompathManager
from pybel import BELGraph
from pybel.dsl import BaseEntity
from pyobo import get_obo_graph, get_terms_from_graph
from .constants import BEL_NAMESPACES, MODULE_NAME
from .models import Annotation, Base, Hierarchy, Synonym, Target, Term
from .parser import get_goa_all_df

logger = logging.getLogger(__name__)


def normalize_go_id(identifier: str) -> str:
    """If a GO term does not start with the ``GO:`` prefix, add it."""
    if not identifier.startswith('GO:'):
        return f'GO:{identifier}'

    return identifier


class Manager(CompathManager):
    """Biological process multi-hierarchy."""

    module_name = MODULE_NAME
    _base: DeclarativeMeta = Base

    pathway_model = Term
    protein_model = Annotation

    namespace_model = Term
    edge_model = [Hierarchy, Annotation]
    identifiers_recommended = 'Gene Ontology'
    identifiers_pattern = r'^GO:\d{7}$'
    identifiers_miriam = 'MIR:00000022'
    identifiers_namespace = 'go'
    identifiers_url = 'http://identifiers.org/go/'

    def __init__(self, *args, **kwargs) -> None:  # noqa: D107
        super().__init__(*args, **kwargs)

        self.go = get_obo_graph('go')
        self.terms = {}
        self.name_id = {}

    def is_populated(self) -> bool:
        """Check if the database is already populated."""
        return 0 < self.count_terms()

    def get_term_by_id(self, go_id: str) -> Optional[Term]:
        """Get a GO entry by its identifier."""
        go_id = normalize_go_id(go_id)
        return self.session.query(Term).filter(Term.identifier == go_id).one_or_none()

    def get_term_by_name(self, name: str) -> Optional[Term]:
        """Get a GO entry by name."""
        return self.session.query(Term).filter(Term.name == name).one_or_none()

    def is_complex(self, identifier) -> bool:
        """Check if a GO term is a complex."""
        return 'GO:0032991' in nx.descendants(self.go, identifier)

    def populate(self, path=None, force_download=False) -> None:
        """Populate the database.

        :param path: Path to the GO OBO file
        :param force_download:
        """
        terms = get_terms_from_graph(self.go)

        for term in tqdm(terms, desc='populating GO terms'):
            is_complex = self.is_complex(term.identifier)

            term_model = self.terms[term.identifier] = Term(
                identifier=term.identifier,
                name=term.name,
                namespace=term.namespace,
                definition=term.definition,
                is_complex=is_complex,
                synonyms=[
                    Synonym(name=synonym.name)
                    for synonym in term.synonyms
                ],
            )
            self.session.add(term_model)

        for term in tqdm(terms, desc='populating GO hierarchy'):
            for parent in term.parents:
                hierarchy = Hierarchy(
                    subject=self.terms[term.identifier],
                    object=self.terms[parent.identifier],
                    relation='isA',
                )
            self.session.add(hierarchy)

        logger.info('building annotations')
        annotation_columns = [
            'go_id',
            'db',
            'db_id',
            'qualifier',
            'provenance',
            'evidence_code',
        ]
        goa_df = get_goa_all_df()

        goa_targets_df = goa_df[['db', 'db_id', 'db_symbol', 'taxonomy_id']].drop_duplicates()
        it = tqdm(goa_targets_df.values, total=len(goa_targets_df.index), desc='populating targets')
        curie_to_target = {}
        for db, db_id, db_symbol, taxonomy_id in it:
            hgnc_id, hgnc_symbol = None, None
            if db == 'UniProtKB':
                hgnc_symbol = get_gene_name(db_id)
                if hgnc_symbol:
                    hgnc_id = hgnc_name_to_id.get(hgnc_symbol)

            curie_to_target[db, db_id] = target = Target(
                db=db, db_id=db_id, db_symbol=db_symbol, taxonomy_id=taxonomy_id[len('taxon:'):],
                hgnc_id=hgnc_id, hgnc_symbol=hgnc_symbol,
            )
            self.session.add(target)

        it = tqdm(goa_df[annotation_columns].values, total=len(goa_df.index), desc='populating GO annotations')
        for go_id, db, db_id, qualifier, provenance, evidence_code in it:
            if pd.notna(provenance):
                provenance_db, provenance_id = provenance.split(':')
            else:
                provenance_db, provenance_id = None, None
            annotation = Annotation(
                term=self.terms[go_id],
                target=curie_to_target[db, db_id],
                qualifier=qualifier,
                provenance_db=provenance_db,
                provenance_id=provenance_id,
                evidence_code=evidence_code,
            )
            self.session.add(annotation)

        t = time.time()
        logger.info('committing models')
        self.session.commit()
        logger.info('committed models in %.2f seconds', time.time() - t)

    def count_terms(self) -> int:
        """Count the number of entries in GO."""
        return self._count_model(Term)

    def count_synonyms(self) -> int:
        """Count the number of synonyms in GO."""
        return self._count_model(Synonym)

    def count_hierarchies(self) -> int:
        """Count the number of synonyms in GO."""
        return self._count_model(Hierarchy)

    def list_hierarchies(self) -> List[Hierarchy]:
        """List hierarchy entries."""
        return self._list_model(Hierarchy)

    def count_annotations(self) -> int:
        """Count the number of annotations."""
        return self._count_model(Annotation)

    def list_annotations(self) -> List[Annotation]:
        """List annotation entries."""
        return self._list_model(Annotation)

    def summarize(self) -> Mapping[str, int]:
        """Return a summary dictionary over the content of the database."""
        return dict(
            terms=self.count_terms(),
            synonyms=self.count_synonyms(),
            hierarchies=self.count_hierarchies(),
            annotations=self.count_annotations(),
        )

    def export_gene_sets(self, use_tqdm: bool = True) -> Mapping[str, Set[str]]:
        """Return the pathway - genesets mapping."""
        self._query_pathway().all()
        rv = defaultdict(set)
        targets = self.session.query(Target.id).filter(Target.hgnc_symbol.isnot(None))
        terms = self.session.query(Term.name, Target.hgnc_symbol).join(Term.annotations).join(Annotation.target).filter(
            Target.id.in_(targets))
        for name, hgnc_symbol in tqdm(terms):
            rv[name].add(hgnc_symbol)
        return dict(rv)

    def lookup_term(self, node: pybel.dsl.BaseAbundance) -> Optional[Term]:
        """Guess the identifier from a PyBEL node data dictionary."""
        namespace = node.namespace

        if namespace is None or namespace.upper() not in BEL_NAMESPACES:
            return

        identifier = node.identifier
        if identifier:
            return self.get_term_by_id(identifier)

        model = self.get_term_by_id(node.name)
        if model is not None:
            return model

        return self.get_term_by_name(node.name)

    def iter_terms(self, graph: BELGraph, use_tqdm: bool = False) -> Iterable[Tuple[BaseEntity, Term]]:
        """Iterate over nodes in the graph that can be looked up."""
        it = (
            tqdm(graph, desc='GO terms')
            if use_tqdm else
            graph
        )
        for node in it:
            term = self.lookup_term(node)
            if term is not None:
                yield node, term

    def normalize_terms(self, graph: BELGraph, use_tqdm: bool = False) -> None:
        """Add identifiers to all GO terms."""
        mapping = {}

        for node, term in list(self.iter_terms(graph, use_tqdm=use_tqdm)):
            try:
                dsl = term.to_pybel()
            except ValueError:
                logger.warning('deleting GO node %r', node)
                graph.remove_node(node)
                continue
            else:
                mapping[node] = dsl

        nx.relabel_nodes(graph, mapping, copy=False)

    def enrich_bioprocesses(self, graph: BELGraph, use_tqdm: bool = False) -> None:
        """Enrich a BEL graph's biological processes."""
        self.add_namespace_to_graph(graph)
        for node, term in list(self.iter_terms(graph, use_tqdm=use_tqdm)):
            if not isinstance(node, pybel.dsl.BiologicalProcess):
                continue

            for hierarchy in term.in_edges:
                graph.add_is_a(hierarchy.subject.to_pybel(), node)

            for hierarchy in term.out_edges:
                graph.add_is_a(node, hierarchy.object.to_pybel())

    def get_release_date(self) -> str:
        """Convert the OBO release date to a ISO 8601 version.

        Example: 'releases/2017-03-26'
        """
        release_time = time.strptime(self.go.graph['data-version'], 'releases/%Y-%m-%d')
        return time.strftime('%Y%m%d', release_time)

    def to_bel(self) -> BELGraph:
        """Convert Gene Ontology to BEL, with given strategies."""
        graph = BELGraph(
            name='Gene Ontology',
            version=self.get_release_date(),
        )

        for hierarchy in tqdm(self.list_hierarchies(), total=self.count_hierarchies(),
                              desc='Mapping GO hierarchy to BEL'):
            hierarchy.add_to_graph(graph)

        for annotation in tqdm(self.list_annotations(), total=self.count_annotations(),
                               desc='Mapping GO annotations to BEL'):
            annotation.add_to_graph(graph)

        return graph

    def _add_admin(self, app, **kwargs):
        """Add admin methods."""
        from flask_admin import Admin
        from flask_admin.contrib.sqla import ModelView

        class TermView(ModelView):
            """Pathway view in Flask-admin."""

            column_searchable_list = (
                Term.identifier,
                Term.name
            )

        class TargetView(ModelView):
            """Protein view in Flask-admin."""

            column_searchable_list = (
                Target.db_id,
                Target.db_symbol,
                Target.hgnc_id,
                Target.hgnc_symbol,
            )

        admin = Admin(app, **kwargs)
        admin.add_view(TermView(Term, self.session))
        admin.add_view(TargetView(Target, self.session))
        admin.add_view(ModelView(Annotation, self.session))
        admin.add_view(ModelView(Hierarchy, self.session))
        return admin
