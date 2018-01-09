# -*- coding: utf-8 -*-

import os
from urllib.request import urlretrieve

import obonet

from .constants import GO_OBO_FILE, GO_OBO_URL


def download_go_obo(force_download=False):
    """Downloads the GO OBO file

    :param force_download: bool to force download
    """
    if not os.path.exists(GO_OBO_FILE) or force_download:
        urlretrieve(GO_OBO_URL, GO_OBO_FILE)

    return GO_OBO_FILE


def get_go(path=None, force_download=False):
    """Interface to download and parse a GO obo file with :mod:`obonet`.

    :param Optional[str] path: path to the file
    :param Optional[bool] force_download: True to force download resources
    :rtype: networkx.MultiDiGraph
    """
    if path is None:
        path = download_go_obo(force_download=force_download)

    return obonet.read_obo(path)
