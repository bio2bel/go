# -*- coding: utf-8 -*-

"""Parser(s) for Gene Ontology."""

import logging

import pandas as pd

from bio2bel.downloading import make_df_getter
from .constants import (
    GAF_COLUMNS, GO_HUMAN_ANNOTATIONS_PATH, GO_HUMAN_ANNOTATIONS_URL, GO_HUMAN_COMPLEX_ANNOTATIONS_PATH,
    GO_HUMAN_COMPLEX_ANNOTATIONS_URL, GO_HUMAN_ISOFORM_ANNOTATIONS_PATH, GO_HUMAN_ISOFORM_ANNOTATIONS_URL,
    GO_HUMAN_RNA_ANNOTATIONS_PATH, GO_HUMAN_RNA_ANNOTATIONS_URL,
)

logger = logging.getLogger(__name__)

__all__ = [
    'get_goa_human_df',
    'get_goa_human_complex_df',
    'get_goa_human_isoform_df',
    'get_goa_human_rna_df',
    'get_goa_all_df',
]


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
    df = pd.concat([
        get_goa_human_rna_df(),
        get_goa_human_complex_df(),
        get_goa_human_isoform_df(),
        get_goa_human_df(),
    ])
    return df[df['go_id'].notna()]


def get_goa_human_complex_processed_(**kwargs):
    df = get_goa_human_complex_df(**kwargs)
    df.db_synonym = df.db_synonym.map(lambda s: s.split('|') if pd.notna(s) else s)
    df.annotation_extensions = df.annotation_extensions.map(lambda s: s.split(',') if pd.notna(s) else s)
    return df
