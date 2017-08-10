# -*- coding: utf-8 -*-

import logging

import obonet

from pybel_tools import pipeline
from pybel_tools.integration import NodeAnnotator

__all__ = [
    'GOAnnotator',
    'go_annotator',
]

log = logging.getLogger(__name__)

url = 'http://purl.obolibrary.org/obo/go/go-basic.obo'


class GOAnnotator(NodeAnnotator):
    """Annotates GO entries"""

    def __init__(self, preload=True):
        """
        :param bool preload: Should the data be preloaded?
        """
        super(GOAnnotator, self).__init__([
            'GOBP',
            'GOBPID',
            'GOCC',
            'GOCCID',
            'GOMF',
            'GOMFID',
        ])

        #: A dictionary of {str go term/id: str description}
        self.descriptions = {}

        self.id_to_name = {}
        self.name_to_id = {}

        if preload:
            self.download_successful = self.download()

    # OVERRIDES
    def get_description(self, name):
        return self.descriptions.get(name)

    def download(self):
        """Downloads the OBO file for Gene Ontology. Returns true on success."""
        try:
            graph = obonet.read_obo(url)
        except:
            log.exception('Unable to download Gene Ontology OBO')
            return False

        self.id_to_name = {id_: data['name'] for id_, data in graph.nodes(data=True)}
        self.name_to_id = {data['name']: id_ for id_, data in graph.nodes(data=True)}

        for id_, data in graph.nodes(data=True):
            self.descriptions[data['name']] = data['def']
            self.descriptions[id_] = data['def']

        return True


go_annotator = GOAnnotator(preload=False)


@pipeline.in_place_mutator
def annotate_go(graph):
    """Annotate GO entities in the graph

    :param pybel.BELGraph graph: A BEL Graph
    """
    go_annotator.populate_by_graph(graph)
    go_annotator.annotate(graph)
