# -*- coding: utf-8 -*-

"""Parser(s) for Gene Ontology."""

import logging
import os
from typing import Optional

import obonet
import pandas as pd
from networkx import MultiDiGraph, read_gpickle, write_gpickle

from bio2bel.downloading import make_df_getter, make_downloader
from .constants import (
    GAF_COLUMNS, GO_HUMAN_ANNOTATIONS_PATH, GO_HUMAN_ANNOTATIONS_URL, GO_HUMAN_COMPLEX_ANNOTATIONS_PATH,
    GO_HUMAN_COMPLEX_ANNOTATIONS_URL, GO_HUMAN_ISOFORM_ANNOTATIONS_PATH, GO_HUMAN_ISOFORM_ANNOTATIONS_URL,
    GO_HUMAN_RNA_ANNOTATIONS_PATH, GO_HUMAN_RNA_ANNOTATIONS_URL, GO_OBO_PATH, GO_OBO_PICKLE_PATH, GO_OBO_URL,
)

log = logging.getLogger(__name__)

__all__ = [
    'download_go_obo',
    'get_go_from_obo',
    'get_goa_human_df',
    'get_goa_human_complex_df',
    'get_goa_human_isoform_df',
    'get_goa_human_rna_df',
    'get_goa_all_df',
]

download_go_obo = make_downloader(GO_OBO_URL, GO_OBO_PATH)


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


def make_goa_df_getter(url, path):
    return make_df_getter(
        url,
        path,
        sep='\t',
        names=GAF_COLUMNS,
        skiprows=15,
    )


get_goa_human_df = make_goa_df_getter(GO_HUMAN_ANNOTATIONS_URL, GO_HUMAN_ANNOTATIONS_PATH)
get_goa_human_complex_df = make_goa_df_getter(GO_HUMAN_COMPLEX_ANNOTATIONS_URL, GO_HUMAN_COMPLEX_ANNOTATIONS_PATH)
get_goa_human_isoform_df = make_goa_df_getter(GO_HUMAN_ISOFORM_ANNOTATIONS_URL, GO_HUMAN_ISOFORM_ANNOTATIONS_PATH)
get_goa_human_rna_df = make_goa_df_getter(GO_HUMAN_RNA_ANNOTATIONS_URL, GO_HUMAN_RNA_ANNOTATIONS_PATH)


def get_goa_all_df() -> pd.DataFrame:
    """Get all GO annotations as a dataframe."""
    return pd.concat([
        get_goa_human_isoform_df(),
        get_goa_human_isoform_df(),
        get_goa_human_rna_df(),
        get_goa_human_df(),
    ])


def get_goa_human_complex_processed_(**kwargs):
    df = get_goa_human_complex_df(**kwargs)
    df.db_synonym = df.db_synonym.map(lambda s: s.split('|') if pd.notna(s) else s)
    df.annotation_extensions = df.annotation_extensions.map(lambda s: s.split(',') if pd.notna(s) else s)
    return df
