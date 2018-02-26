# -*- coding: utf-8 -*-

import logging
import os
import time

import networkx as nx

from bio2bel_go.parser import get_go
from pybel import BELGraph
from pybel.constants import BIOPROCESS, FUNCTION, IDENTIFIER, IS_A, NAME, NAMESPACE
from pybel.dsl import bioprocess, complex_abundance
from pybel.resources.arty import get_latest_arty_namespace
from .constants import GO_OBO_PICKLE_PATH, MODULE_NAME

log = logging.getLogger(__name__)

GO = MODULE_NAME.upper()

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
    :param pybel.BELGraph graph: BEL Graph
    :param child: PyBEL node tuple (child node)
    :type child: tuple or dict
    """
    for _, parent_identifier in go.out_edges_iter(identifier):
        graph.add_unqualified_edge(  # TODO switch to graph.add_is_a
            child,
            bioprocess(namespace=GO, name=go.node[parent_identifier]['name'], identifier=parent_identifier),
            IS_A
        )


class Manager(object):
    def __init__(self):
        self.go = None
        self.name_id = {}

        if os.path.exists(GO_OBO_PICKLE_PATH):
            self.populate()

    def populate(self, path=None, force_download=False):
        if self.go is None:
            self.go = get_go(path=path, force_download=force_download)

            self.name_id = {
                data['name']: identifier
                for identifier, data in self.go.nodes_iter(data=True)
            }

    def count_entries(self):
        """Counts the number of entries in the GO hierarchy

        :rtype: int
        """
        return self.go.number_of_nodes()

    def summarize(self):
        """Returns a summary dictionary over the content of the database

        :rtype: dict[str,int]
        """
        return dict(entries=self.count_entries())

    def get_go_by_id(self, identifier):
        """Gets a GO entry by its identifier

        :param str identifier:
        :rtype: Optional[dict]
        """
        if not identifier.startswith('GO:'):
            identifier = 'GO:' + identifier

        rv = self.go.node.get(identifier)

        if rv is None:
            return

        rv['id'] = identifier

        return rv

    def get_go_by_name(self, name):
        """Gets a GO entry by name

        :param str name:
        :rtype: Optional[dict]
        """
        identifier = self.name_id.get(name)

        if identifier is None:
            return

        return self.get_go_by_id(identifier)

    def guess_identifier(self, data):
        """Guesses the identifier from a PyBEL node data dictionary

        :param dict data:
        :rtype: Optional[str]
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

    def enrich_bioprocesses(self, graph):
        """Enriches a BEL Graph?

        :type graph: pybel.BELGraph
        """
        if self.go is None:
            self.populate()

        for node, data in graph.nodes(data=True):
            if data[FUNCTION] != BIOPROCESS:
                continue

            identifier = self.guess_identifier(data)

            if identifier:
                add_parents(self.go, identifier, graph, child=node)

    def get_release_date(self):
        """Converts the OBO release date to a ISO 8601 version. Example: 'releases/2017-03-26'"""
        t = time.strptime(self.go.graph['data-version'], 'releases/%Y-%m-%d')
        return time.strftime('%Y%m%d', t)

    def to_bel(self):
        """Converts Gene Ontology to BEL, with given strategies

        :rtype: pybel.BELGraph
        """
        if self.go is None:
            self.populate()

        rv = BELGraph(
            name='Gene Ontology',
            version=self.get_release_date(),
            description='Gene Ontology: the framework for the model of biology. The GO defines concepts/classes used '
                        'to describe gene function, and relationships between these concepts',
            authors='Gene Ontology Consortium'
        )

        rv.namespace_url[GO] = get_latest_arty_namespace('go')

        for identifier, data in self.go.nodes(data=True):
            name = data.get('name')

            if name is None:
                log.warning('missing name: %s', identifier)
                continue

            namespace = data['namespace']

            if namespace == 'biological_process':
                add_parents(self.go, identifier, rv, child=gobp(self.go, identifier))

            elif 'GO:0032991' in nx.descendants(self.go, identifier):  # GO:0032991 is "macromolecular complex"
                add_parents(self.go, identifier, rv, child=gocc(self.go, identifier))

        return rv


def gocc(go, identifier):
    """Makes a GO complex node

    :rtype: complex_abundance
    """
    return complex_abundance(namespace=GO, name=go.node[identifier]['name'], identifier=identifier, members=[])


def gobp(go, identifier):
    """Makes a GO biological process node

    :rtype: bioprocess
    """
    return bioprocess(namespace=GO, name=go.node[identifier]['name'], identifier=identifier)
