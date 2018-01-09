# -*- coding: utf-8 -*-

import unittest

from bio2bel_go.enrich import enrich
from pybel import BELGraph
from pybel.dsl import bioprocess


class TestEnrich(unittest.TestCase):
    """Tests functions that enrich BEL graph's contents related to Gene Ontology"""

    def test_enrich(self):
        graph = BELGraph()

        graph.add_node_from_data(bioprocess(namespace='GO', name='asaggsag'))

        enrich(graph)

        # TODO test stuff!
