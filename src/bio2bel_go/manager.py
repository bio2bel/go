# -*- coding: utf-8 -*-

import logging
import time

import networkx as nx

from bio2bel_go.parser import get_go
from pybel import BELGraph
from pybel.constants import BIOPROCESS, FUNCTION, IS_A, NAME, NAMESPACE
from pybel.dsl import bioprocess, complex_abundance
from pybel.resources.arty import get_latest_arty_namespace
from .constants import MODULE_NAME

log = logging.getLogger(__name__)

GO = MODULE_NAME.upper()


def add_parents(go, identifier, graph, child):
    """

    :param go: GO Network
    :param identifier: GO Identifier
    :param pybel.BELGraph graph: BEL Graph
    :param child: PyBEL node tuple (child node)
    :type child: tuple or dict
    """
    for _, parent_identifier in go.out_edges_iter(identifier):
        graph.add_unqualified_edge(
            child,
            bioprocess(namespace=GO, name=go.node[parent_identifier]['name'], identifier=parent_identifier),
            IS_A
        )


class Manager(object):
    def __init__(self, autopopulate=False):
        self.go = None

        if autopopulate:
            self.populate()

    def populate(self, path=None, force_download=False):
        if self.go is None:
            self.go = get_go(path=path, force_download=force_download)

    def enrich_bioprocesses(self, graph):
        """Enriches a BEL Graph?

        :type graph: pybel.BELGraph
        """
        if self.go is None:
            self.populate()

        name_id = {
            data['name']: node
            for node, data in self.go.nodes_iter(data=True)
        }

        for node, data in graph.nodes(data=True):
            if data[FUNCTION] != BIOPROCESS:
                continue

            namespace = data.get(NAMESPACE)

            if namespace is None:
                continue

            name = data.get(NAME)

            if namespace in {'GO', 'GOBP', 'GOBPID'}:
                if name in name_id:
                    add_parents(self.go, name_id[name], graph, child=node)
                elif name in self.go:
                    add_parents(self.go, name, graph, child=node)

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

        rv.namespace_url[GO] = get_latest_arty_namespace(GO)

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
