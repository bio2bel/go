# -*- coding: utf-8 -*-

import logging
import unittest

from pybel import BELGraph
from pybel.dsl import bioprocess
from tests.constants import TemporaryCacheClass

log = logging.getLogger(__name__)


class TestEnrich(TemporaryCacheClass):
    """Tests functions that enrich BEL graph's contents related to Gene Ontology"""

    @classmethod
    def populate(cls):
        cls.manager.populate()

    def setUp(self):
        self.graph = BELGraph()

    def help_test_cell_proliferation(self, graph):
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_bioprocesses(graph)

        self.assertEqual(2, graph.number_of_nodes(), msg='parent biological process was not added')
        self.assertEqual(1, graph.number_of_edges())

    def test_enrich_go_name(self):
        self.graph.add_node_from_data(bioprocess(namespace='GO', name='cell proliferation'))

        self.help_test_cell_proliferation(self.graph)

    def test_enrich_gobp_name(self):
        self.graph.add_node_from_data(bioprocess(namespace='GOBP', name='cell proliferation'))

        self.help_test_cell_proliferation(self.graph)

    def test_enrich_go_identifier(self):
        self.graph.add_node_from_data(bioprocess(namespace='GO', identifier='GO:0008283'))

        self.help_test_cell_proliferation(self.graph)


if __name__ == '__main__':
    unittest.main()
