# -*- coding: utf-8 -*-

"""Parser(s) for Gene Ontology."""

import logging
import os
from typing import Optional
from urllib.request import urlretrieve

import obonet
from networkx import MultiDiGraph, read_gpickle, write_gpickle

from .constants import GO_OBO_PATH, GO_OBO_PICKLE_PATH, GO_OBO_URL

log = logging.getLogger(__name__)

__all__ = [
    'download_go_obo',
    'get_go_from_obo',
]


def download_go_obo(force_download: bool = False):
    """Download the GO OBO file.

    :param force_download: bool to force download
    """
    if os.path.exists(GO_OBO_PATH) and not force_download:
        log.info('using cached obo file at %s', GO_OBO_PATH)
    else:
        log.info('downloading %s to %s', GO_OBO_URL, GO_OBO_PATH)
        urlretrieve(GO_OBO_URL, GO_OBO_PATH)

    return GO_OBO_PATH


def get_go_from_obo(path: Optional[str] = None, force_download: bool = False) -> MultiDiGraph:
    """Download and parse a GO obo file with :mod:`obonet` into a MultiDiGraph.

    :param path: path to the file
    :param force_download: True to force download resources
    """
    if path is None and os.path.exists(GO_OBO_PICKLE_PATH) and not force_download:
        log.info('loading from %s', GO_OBO_PICKLE_PATH)
        return read_gpickle(GO_OBO_PICKLE_PATH)

    if path is not None:
        return obonet.read_obo(path)

    path = download_go_obo(force_download=force_download)

    log.info('reading OBO')
    result = obonet.read_obo(path)

    log.info('caching pickle to %s', GO_OBO_PICKLE_PATH)
    write_gpickle(result, GO_OBO_PICKLE_PATH)

    return result
