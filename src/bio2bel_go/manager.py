# -*- coding: utf-8 -*-

"""Manager for Bio2BEL GO."""

import logging
import time
from typing import Iterable, List, Mapping, Optional, Tuple

import networkx as nx
from pybel import BELGraph
from pybel.constants import BIOPROCESS, FUNCTION, NAMESPACE
from pybel.dsl import BaseEntity
from pybel.manager.models import Namespace, NamespaceEntry
from sqlalchemy.ext.declarative import DeclarativeMeta
from tqdm import tqdm

from bio2bel import AbstractManager
from bio2bel.manager.bel_manager import BELManagerMixin
from bio2bel.manager.flask_manager import FlaskMixin
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
from .constants import BEL_NAMESPACES, MODULE_NAME
from .dsl import gobp
from .models import Annotation, Base, Hierarchy, Synonym, Term
from .parser import get_go_from_obo, get_goa_all_df

log = logging.getLogger(__name__)


def add_parents(go, identifier: str, graph: BELGraph, child: BaseEntity):
    """Add parents to the network.

    :param go: GO Network
    :param identifier: GO Identifier of the child
    :param graph: A BEL graph
    :param child: A BEL node
    """
    for _, parent_identifier in go.out_edges(identifier):
        graph.add_is_a(child, gobp(go, identifier))


def normalize_go_id(identifier: str) -> str:
    """If a GO term does not start with the ``GO:`` prefix, add it."""
    if not identifier.startswith('GO:'):
        return f'GO:{identifier}'

    return identifier


class Manager(AbstractManager, BELManagerMixin, BELNamespaceManagerMixin, FlaskMixin):
    """Biological process multi-hierarchy."""

    module_name = MODULE_NAME
    _base: DeclarativeMeta = Base
    flask_admin_models = [Term, Hierarchy, Synonym, Annotation]

    namespace_model = Term
    edge_model = [Hierarchy, Annotation]
    identifiers_recommended = 'Gene Ontology'
    identifiers_pattern = r'^GO:\d{7}$'
    identifiers_miriam = 'MIR:00000022'
    identifiers_namespace = 'go'
    identifiers_url = 'http://identifiers.org/go/'

    def __init__(self, *args, **kwargs) -> None:  # noqa: D107
        super().__init__(*args, **kwargs)

        self.go = None
        self.terms = {}
        self.name_id = {}

    def is_populated(self) -> bool:
        """Check if the database is already populated."""
        return 0 < self.count_terms()

    def get_term_by_id(self, go_id: str) -> Optional[Term]:
        """Get a GO entry by its identifier."""
        go_id = normalize_go_id(go_id)
        return self.session.query(Term).filter(Term.go_id == go_id).one_or_none()

    def get_term_by_name(self, name: str) -> Optional[Term]:
        """Get a GO entry by name."""
        return self.session.query(Term).filter(Term.name == name).one_or_none()

    def populate(self, path=None, force_download=False) -> None:
        """Populate the database.

        :param path: Path to the GO OBO file
        :param force_download:
        """
        self.go = get_go_from_obo(path=path, force_download=force_download)

        log.info('building terms')
        for go_id, data in tqdm(self.go.nodes(data=True), total=self.go.number_of_nodes(), desc='Terms'):
            is_complex = 'GO:0032991' in nx.descendants(self.go, go_id)

            term = self.terms[go_id] = Term(
                go_id=go_id,
                name=data['name'],
                namespace=data['namespace'],
                definition=data['def'],
                is_complex=is_complex,
                synonyms=[
                    Synonym(name=name)
                    for name in data.get('synonym', [])
                ],
            )
            self.session.add(term)

        log.info('building hierarchy')
        for sub_id, obj_id, data in tqdm(self.go.edges(data=True), total=self.go.number_of_edges(), desc='Edges'):
            hierarchy = Hierarchy(
                subject=self.terms[sub_id],
                object=self.terms[obj_id],
            )
            self.session.add(hierarchy)

        log.info('building annotations')
        annotation_columns = [
            'go_id',
            'db',
            'db_id',
            'db_symbol',
            'qualifier',
            'provenance',
            'evidence_code',
            'taxonomy_id',
        ]
        goa_df = get_goa_all_df()

        it = tqdm(goa_df[annotation_columns].values, total=len(goa_df.index), desc='Annotations')
        for go_id, db, db_id, db_symbol, qualifier, provenance, evidence_code, taxonomy_id in it:
            provenance_db, provenance_id = provenance.split(':')
            annotation = Annotation(
                term=self.terms[go_id],
                db=db,
                db_id=db_id,
                db_symbol=db_symbol,
                qualifier=qualifier,
                provenance_db=provenance_db,
                provenance_id=provenance_id,
                evidence_code=evidence_code,
                tax_id=taxonomy_id,
            )
            self.session.add(annotation)

        t = time.time()
        log.info('committing models')
        self.session.commit()
        log.info('committed models in %.2f seconds', time.time() - t)

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

    def lookup_term(self, node: BaseEntity) -> Optional[Term]:
        """Guess the identifier from a PyBEL node data dictionary."""
        namespace = node.get(NAMESPACE)

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
                dsl = term.as_bel()
            except ValueError:
                log.warning('deleting GO node %r', node)
                graph.remove_node(node)
                continue
            else:
                mapping[node] = dsl

        nx.relabel_nodes(graph, mapping, copy=False)

    def enrich_bioprocesses(self, graph: BELGraph, use_tqdm: bool = False) -> None:
        """Enrich a BEL graph's biological processes."""
        self.add_namespace_to_graph(graph)
        for node, term in list(self.iter_terms(graph, use_tqdm=use_tqdm)):
            if node[FUNCTION] != BIOPROCESS:
                continue

            for hierarchy in term.in_edges:
                graph.add_is_a(hierarchy.subject.as_bel(), node)

            for hierarchy in term.out_edges:
                graph.add_is_a(node, hierarchy.object.as_bel())

    def get_release_date(self) -> str:
        """Convert the OBO release date to a ISO 8601 version.

        Example: 'releases/2017-03-26'
        """
        release_time = time.strptime(self.go.graph['data-version'], 'releases/%Y-%m-%d')
        return time.strftime('%Y%m%d', release_time)

    def _get_identifier(self, model: Term) -> str:
        return model.go_id

    def _create_namespace_entry_from_model(self, term: Term, namespace: Namespace) -> NamespaceEntry:
        return NamespaceEntry(
            name=term.name,
            identifier=term.go_id,
            encoding=term.bel_encoding,
            namespace=namespace,
        )

    def to_bel(self) -> BELGraph:
        """Convert Gene Ontology to BEL, with given strategies."""
        graph = BELGraph(
            name='Gene Ontology',
            version='1.0.0',
            description='Gene Ontology: the framework for the model of biology. The GO defines concepts/classes used '
                        'to describe gene function, and relationships between these concepts',
            authors='Gene Ontology Consortium'
        )

        self.add_namespace_to_graph(graph)

        for hierarchy in tqdm(self.list_hierarchies(), total=self.count_hierarchies(),
                              desc='Mapping GO hierarchy to BEL'):
            hierarchy.add_to_graph(graph)

        for annotation in tqdm(self.list_annotations(), total=self.count_annotations(),
                               desc='Mapping GO annotations to BEL'):
            annotation.add_to_graph(graph)

        return graph
