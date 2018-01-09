# -*- coding: utf-8 -*-

import unittest

from bio2bel_go import Manager
from pybel import BELGraph
from pybel.dsl import bioprocess


class TestEnrich(unittest.TestCase):
    """Tests functions that enrich BEL graph's contents related to Gene Ontology"""

    @classmethod
    def setUpClass(cls):
        cls.manager = Manager()
        cls.manager.populate()  # FIXME use test data?

    def help_test_cell_proliferation(self, graph):
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_bioprocesses(graph)

        self.assertEqual(2, graph.number_of_nodes())
        self.assertEqual(1, graph.number_of_edges())

    def test_enrich_go_name(self):
        graph = BELGraph()
        graph.add_node_from_data(bioprocess(namespace='GO', name='cell proliferation'))

        self.help_test_cell_proliferation(graph)

    def test_enrich_gobp_name(self):
        graph = BELGraph()
        graph.add_node_from_data(bioprocess(namespace='GOBP', name='cell proliferation'))

        self.help_test_cell_proliferation(graph)

    def test_enrich_go_identifier(self):
        graph = BELGraph()
        graph.add_node_from_data(bioprocess(namespace='GO', identifier='0008283'))

        self.help_test_cell_proliferation(graph)
