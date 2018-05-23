# -*- coding: utf-8 -*-

"""Manager for Bio2BEL GO."""

import logging
import time
from typing import List, Optional

import networkx as nx
from tqdm import tqdm

from bio2bel.namespace_manager import NamespaceManagerMixin
from pybel import BELGraph
from pybel.constants import BIOPROCESS, FUNCTION, IDENTIFIER, NAME, NAMESPACE
from pybel.manager.models import NamespaceEntry
from .constants import MODULE_NAME
from .dsl import gobp
from .models import Base, Hierarchy, Synonym, Term
from .parser import get_go

log = logging.getLogger(__name__)

BEL_NAMESPACES = {
    'GO',
    'GOBP',
    'GOBPID',
    'GOCC',
    'GOCCID',
    'GOMF',
    'GOMFID',
}


def add_parents(go, identifier, graph, child):
    """
    :param go: GO Network
    :param identifier: GO Identifier of the child
    :param pybel.BELGraph graph: A BEL graph
    :param BaseEntity child: A BEL node
    """
    for _, parent_identifier in go.out_edges(identifier):
        graph.add_is_a(child, gobp(go, identifier))


_go_prefix = 'GO:'


def normalize_go_id(identifier: str) -> str:
    if identifier.startswith(_go_prefix):
        return identifier[len(_go_prefix):]
    return identifier


class Manager(NamespaceManagerMixin):
    """Manager for Bio2BEL GO."""

    module_name = MODULE_NAME
    flask_admin_models = [Term, Hierarchy, Synonym]
    namespace_model = Term

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.go = None
        self.terms = {}
        self.name_id = {}

    @property
    def _base(self):
        return Base

    def is_populated(self) -> bool:
        """Check if the database is already populated"""
        return 0 < self.count_terms()

    def get_term_by_id(self, go_id) -> Optional[Term]:
        """Gets a GO entry by its identifier

        :param str go_id:
        :rtype: Optional[dict]
        """
        go_id = normalize_go_id(go_id)
        return self.session.query(Term).filter(Term.go_id == go_id).one_or_none()

    def populate(self, path=None, force_download=False):
        self.go = get_go(path=path, force_download=force_download)

        log.info('building terms')
        for go_id, data in tqdm(self.go.nodes(data=True), total=self.go.number_of_nodes(), desc='Terms'):
            is_complex = 'GO:0032991' in nx.descendants(self.go, go_id)

            normalized_go_id = normalize_go_id(go_id)

            term = self.terms[normalized_go_id] = Term(
                go_id=normalized_go_id,
                name=data['name'],
                namespace=data['namespace'],
                definition=data['def'],
                is_complex=is_complex,
                synonyms=[
                    Synonym(name=name)
                    for name in data.get('synonym', [])
                ]
            )
            self.session.add(term)

        log.info('building hierarchy')
        for sub_id, obj_id, data in tqdm(self.go.edges(data=True), total=self.go.number_of_edges(), desc='Edges'):
            hierarchy = Hierarchy(
                subject=self.terms[normalize_go_id(sub_id)],
                object=self.terms[normalize_go_id(obj_id)]
            )
            self.session.add(hierarchy)

        t = time.time()
        log.info('committing models')
        self.session.commit()
        log.info('committed models in %.2f seconds', time.time() - t)

    def count_terms(self) -> int:
        """Counts the number of entries in the GO hierarchy

        :rtype: int
        """
        return self._count_model(Term)

    def count_synonyms(self) -> int:
        """Counts the number of synonyms in the GO hierarchy

        :rtype: int
        """
        return self._count_model(Synonym)

    def count_hierarchies(self) -> int:
        """Counts the number of synonyms in the GO hierarchy

        :rtype: int
        """
        return self._count_model(Hierarchy)

    def list_hierarchies(self) -> List[Hierarchy]:
        return self._list_model(Hierarchy)

    def summarize(self):
        """Returns a summary dictionary over the content of the database

        :rtype: dict[str,int]
        """
        return dict(
            terms=self.count_terms(),
            synonyms=self.count_synonyms(),
            hierarchies=self.count_hierarchies(),
        )

    def get_term_by_name(self, name) -> Optional[Term]:
        """Gets a GO entry by name

        :param str name:
        :rtype: Optional[dict]
        """
        identifier = self.name_id.get(name)

        if identifier is None:
            return

        return self.get_term_by_id(identifier)

    def guess_identifier(self, data) -> Optional[str]:
        """Guesses the identifier from a PyBEL node data dictionary

        :param dict data:
        """
        namespace = data.get(NAMESPACE)

        if namespace is None:
            raise ValueError('namespace must not be None')

        if namespace not in BEL_NAMESPACES:
            raise ValueError('namespace is not valid for GO: {}'.format(namespace))

        identifier = data.get(IDENTIFIER)

        if identifier:
            if identifier in self.go:
                return identifier

            if not identifier.startswith('GO:'):
                augumented_identifier = 'GO:{}'.format(identifier)

                if augumented_identifier in self.go:
                    return augumented_identifier

        name = data.get(NAME)

        if name is None:
            raise ValueError

        if name in self.name_id:
            return self.name_id[name]

        if name in self.go:
            return name

        augumented_identifier = 'GO:{}'.format(identifier)

        if augumented_identifier in self.go:
            return augumented_identifier

    def enrich_bioprocesses(self, graph: BELGraph):
        """Enriches a BEL graph's biological processes."""
        if self.go is None:
            self.populate()

        for node, data in graph.nodes(data=True):
            if data[FUNCTION] != BIOPROCESS:
                continue

            identifier = self.guess_identifier(data)

            if identifier:
                add_parents(self.go, identifier, graph, child=node)

    def get_release_date(self) -> str:
        """Converts the OBO release date to a ISO 8601 version. Example: 'releases/2017-03-26'"""
        t = time.strptime(self.go.graph['data-version'], 'releases/%Y-%m-%d')
        return time.strftime('%Y%m%d', t)

    def _get_identifier(self, model):
        return model.go_id

    def _create_namespace_entry_from_model(self, model, namespace):
        rv = NamespaceEntry(name=model.name, identifier=model.go_id, namespace=namespace)

        if model.namespace == 'biological_process':
            rv.encoding = 'B'

        elif model.namespace == 'cellular_component':
            if model.is_complex:
                rv.encoding = 'C'
            else:
                rv.encoding = 'Y'

        elif model.namespace == 'molecular_function':
            rv.encoding = 'F'

        return rv

    def to_bel(self):
        """Converts Gene Ontology to BEL, with given strategies

        :rtype: pybel.BELGraph
        """
        rv = BELGraph(
            name='Gene Ontology',
            version='1.0.0',
            description='Gene Ontology: the framework for the model of biology. The GO defines concepts/classes used '
                        'to describe gene function, and relationships between these concepts',
            authors='Gene Ontology Consortium'
        )

        namespace = self.upload_bel_namespace()
        rv.namespace_url[namespace.keyword] = namespace.url

        for hierarchy in tqdm(self.list_hierarchies(), total=self.count_hierarchies(),
                              desc='Mapping GO hierarchy to BEL'):
            sub = hierarchy.subject.as_bel()
            obj = hierarchy.object.as_bel()

            if sub and obj:
                rv.add_is_a(sub, obj)

        return rv
