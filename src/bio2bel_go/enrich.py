# -*- coding: utf-8 -*-

import logging

from pybel import to_database
from .manager import Manager

__all__ = [
    'to_bel',
    'enrich_bioprocesses'
]

log = logging.getLogger(__name__)


def to_bel(manager=None):
    """Creates a BEL Graph

    :type manager: Optional[bio2bel_go.Manager]
    """
    manager = manager or Manager(autopopulate=True)
    return manager.to_bel()


def enrich_bioprocesses(graph, manager=None):
    """Enriches a BEL Graph?

    :type graph: pybel.BELGraph
    :type manager: Optional[bio2bel_go.Manager]
    """
    manager = manager or Manager(autopopulate=True)
    manager.enrich_bioprocesses(graph)


def upload_bel(manager=None, pybel_manager=None):
    """Uploads BEL to PyBEL edge store

    :type manager: Optional[bio2bel_go.Manager]
    :type pybel_manager: Optional[pybel.Manager]
    :rtype: pybel.manager.models.Network
    """
    log.info('converting bel')
    graph = to_bel(manager=manager)
    log.info('storing')
    return to_database(graph, connection=pybel_manager)
