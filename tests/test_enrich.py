# -*- coding: utf-8 -*-

"""Tests for enrichment."""

from bio2bel_go import Manager
from pybel import BELGraph
from pybel.dsl import bioprocess
from tests.constants import TemporaryCacheClass


class TestEnrich(TemporaryCacheClass):
    """Tests functions that enrich BEL graph's contents related to Gene Ontology."""

    manager: Manager

    def setUp(self):
        """Set up the database with a BEL graph."""
        super().setUp()
        self.graph = BELGraph()

    def help_test_cell_proliferation(self, graph: BELGraph):
        """Help test the GO entry, "cell proliferation", makes it to the database properly."""
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_bioprocesses(graph)

        self.assertEqual(2, graph.number_of_nodes(), msg='parent biological process was not added')
        self.assertEqual(1, graph.number_of_edges())

    def test_enrich_go_name(self):
        """Test lookup by name."""
        self.graph.add_node_from_data(bioprocess(namespace='GO', name='cell proliferation'))

        self.help_test_cell_proliferation(self.graph)

    def test_enrich_gobp_name(self):
        """Test lookup by name with an alternative namespace."""
        self.graph.add_node_from_data(bioprocess(namespace='GOBP', name='cell proliferation'))

        self.help_test_cell_proliferation(self.graph)

    def test_enrich_go_identifier(self):
        """Test lookup by identifier."""
        self.graph.add_node_from_data(bioprocess(namespace='GO', identifier='GO:0008283'))

        self.help_test_cell_proliferation(self.graph)

    def test_enrich_go_identifier_missing_prefix(self):
        """Test lookup by identifier with a missing prefix."""
        self.graph.add_node_from_data(bioprocess(namespace='GO', identifier='0008283'))

        self.help_test_cell_proliferation(self.graph)
