# -*- coding: utf-8 -*-

import logging
import os
from pickle import dump, load
from urllib.request import urlretrieve

import obonet

from .constants import GO_OBO_PATH, GO_OBO_PICKLE_PATH, GO_OBO_URL
from networkx import write_gpickle, read_gpickle
log = logging.getLogger(__name__)

__all__ = [
    'download_go_obo',
    'get_go',
]


def download_go_obo(force_download=False):
    """Downloads the GO OBO file

    :param force_download: bool to force download
    """
    if os.path.exists(GO_OBO_PATH) and not force_download:
        log.info('using cached obo file at %s', GO_OBO_PATH)
    else:
        log.info('downloading %s to %s', GO_OBO_URL, GO_OBO_PATH)
        urlretrieve(GO_OBO_URL, GO_OBO_PATH)

    return GO_OBO_PATH


def get_go(path=None, force_download=False):
    """Interface to download and parse a GO obo file with :mod:`obonet`.

    :param Optional[str] path: path to the file
    :param Optional[bool] force_download: True to force download resources
    :rtype: networkx.MultiDiGraph
    """
    if os.path.exists(GO_OBO_PICKLE_PATH) and not force_download:
        log.info('loading from %s', GO_OBO_PICKLE_PATH)
        return read_gpickle(GO_OBO_PICKLE_PATH)

    if path is None:
        path = download_go_obo(force_download=force_download)

    log.info('parsing pickle')
    result = obonet.read_obo(path)

    log.info('caching pickle to %s', GO_OBO_PICKLE_PATH)
    write_gpickle(result, GO_OBO_PICKLE_PATH)

    return result
