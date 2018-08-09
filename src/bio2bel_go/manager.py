# -*- coding: utf-8 -*-

"""Manager for Bio2BEL GO."""

import logging
import time
from typing import List, Mapping, Optional

import networkx as nx
from bio2bel import AbstractManager
from bio2bel.manager.bel_manager import BELManagerMixin
from bio2bel.manager.flask_manager import FlaskMixin
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
from pybel import BELGraph
from pybel.constants import BIOPROCESS, FUNCTION, IDENTIFIER, NAME, NAMESPACE
from pybel.manager.models import Namespace, NamespaceEntry
from sqlalchemy.ext.declarative import DeclarativeMeta
from tqdm import tqdm

from .constants import MODULE_NAME
from .dsl import gobp
from .models import Base, Hierarchy, Synonym, Term
from .parser import get_go_from_obo

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

GO_BIOLOGICAL_PROCESS = 'biological_process'
GO_CELLULAR_COMPONENT = 'cellular_component'
GO_MOLECULAR_FUNCTION = 'molecular_function'


def add_parents(go, identifier, graph, child):
    """Add parents to the network.

    :param go: GO Network
    :param identifier: GO Identifier of the child
    :param pybel.BELGraph graph: A BEL graph
    :param BaseEntity child: A BEL node
    """
    for _, parent_identifier in go.out_edges(identifier):
        graph.add_is_a(child, gobp(go, identifier))


def normalize_go_id(identifier: str) -> str:
    """If a GO term does not start with the ``GO:`` prefix, add it."""
    if not identifier.startswith('GO:'):
        return f'GO:{identifier}'

    return identifier


class Manager(AbstractManager, BELManagerMixin, BELNamespaceManagerMixin, FlaskMixin):
    """Manager for Bio2BEL GO."""

    module_name = MODULE_NAME
    flask_admin_models = [Term, Hierarchy, Synonym]
    namespace_model = Term

    identifiers_recommended = 'Gene Ontology'
    identifiers_pattern = '^GO:\d{7}$'
    identifiers_miriam = 'MIR:00000022'
    identifiers_namespace = 'go'
    identifiers_url = 'http://identifiers.org/go/'

    def __init__(self, *args, **kwargs) -> None:  # noqa: D107
        super().__init__(*args, **kwargs)

        self.go = None
        self.terms = {}
        self.name_id = {}

    @property
    def _base(self) -> DeclarativeMeta:
        return Base

    def is_populated(self) -> bool:
        """Check if the database is already populated."""
        return 0 < self.count_terms()

    def get_term_by_id(self, go_id) -> Optional[Term]:
        """Get a GO entry by its identifier.

        :param str go_id:
        :rtype: Optional[dict]
        """
        go_id = normalize_go_id(go_id)
        return self.session.query(Term).filter(Term.go_id == go_id).one_or_none()

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
                ]
            )
            self.session.add(term)

        log.info('building hierarchy')
        for sub_id, obj_id, data in tqdm(self.go.edges(data=True), total=self.go.number_of_edges(), desc='Edges'):
            hierarchy = Hierarchy(
                subject=self.terms[sub_id],
                object=self.terms[obj_id]
            )
            self.session.add(hierarchy)

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

    def summarize(self) -> Mapping[str, int]:
        """Return a summary dictionary over the content of the database."""
        return dict(
            terms=self.count_terms(),
            synonyms=self.count_synonyms(),
            hierarchies=self.count_hierarchies(),
        )

    def get_term_by_name(self, name: str) -> Optional[Term]:
        """Get a GO entry by name."""
        identifier = self.name_id.get(name)

        if identifier is None:
            return

        return self.get_term_by_id(identifier)

    def guess_identifier(self, data: dict) -> Optional[str]:
        """Guess the identifier from a PyBEL node data dictionary."""
        namespace = data.get(NAMESPACE)

        if namespace is None:
            raise ValueError('namespace must not be None')

        if namespace not in BEL_NAMESPACES:
            raise ValueError('namespace is not valid for GO: {}'.format(namespace))

        identifier = data.get(IDENTIFIER)

        if identifier:
            nid = normalize_go_id(identifier)
            if nid in self.go:
                return nid

        name = data[NAME]

        if name in self.name_id:
            return self.name_id[name]

        name = normalize_go_id(name)

        if name in self.go:  # if for some reason this was mistakenly used as the name
            return name

    def enrich_bioprocesses(self, graph: BELGraph):
        """Enrich a BEL graph's biological processes."""
        if self.go is None:
            self.populate()

        for node, data in graph.nodes(data=True):
            if data[FUNCTION] != BIOPROCESS:
                continue

            identifier = self.guess_identifier(data)

            if identifier:
                add_parents(self.go, identifier, graph, child=node)

    def get_release_date(self) -> str:
        """Convert the OBO release date to a ISO 8601 version.

        Example: 'releases/2017-03-26'
        """
        release_time = time.strptime(self.go.graph['data-version'], 'releases/%Y-%m-%d')
        return time.strftime('%Y%m%d', release_time)

    def _get_identifier(self, model: Term) -> str:
        return model.go_id

    def _create_namespace_entry_from_model(self, model: Term, namespace: Namespace) -> NamespaceEntry:
        rv = NamespaceEntry(name=model.name, identifier=model.go_id, namespace=namespace)

        if model.namespace == GO_BIOLOGICAL_PROCESS:
            rv.encoding = 'B'

        elif model.namespace == GO_CELLULAR_COMPONENT:
            if model.is_complex:
                rv.encoding = 'C'
            else:
                rv.encoding = 'Y'

        elif model.namespace == GO_MOLECULAR_FUNCTION:
            rv.encoding = 'F'

        return rv

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
            sub = hierarchy.subject.as_bel()
            obj = hierarchy.object.as_bel()

            if sub and obj:
                graph.add_is_a(sub, obj)

        return graph
