# -*- coding: utf-8 -*-

"""Constants for Bio2BEL GO."""

import os

from bio2bel import get_data_dir

MODULE_NAME = 'go'
DATA_DIR = get_data_dir(MODULE_NAME)

#: The web location of the GO OBO file
GO_OBO_URL = 'http://purl.obolibrary.org/obo/go/go-basic.obo'

#: The local cache location where the GO OBO file is stored
GO_OBO_PATH = os.path.join(DATA_DIR, 'go-basic.obo')

#: The local cache location where the parsed and pickled GO OBO file is stored
GO_OBO_PICKLE_PATH = os.path.join(DATA_DIR, 'go-basic.obo.gpickle')

BEL_NAMESPACES = {
    'GO',
    'GOBP',
    'GOBPID',
    'GOCC',
    'GOCCID',
    'GOMF',
    'GOMFID',
}

GO_BIOLOGICAL_PROCESS = 'biological_process'
GO_CELLULAR_COMPONENT = 'cellular_component'
GO_MOLECULAR_FUNCTION = 'molecular_function'

GO_HUMAN_ANNOTATIONS_URL = 'http://geneontology.org/gene-associations/goa_human.gaf.gz'
GO_HUMAN_ANNOTATIONS_PATH = os.path.join(DATA_DIR, 'goa_human.gaf.gz')

GO_HUMAN_COMPLEX_ANNOTATIONS_URL = 'http://geneontology.org/gene-associations/goa_human_complex.gaf.gz'
GO_HUMAN_COMPLEX_ANNOTATIONS_PATH = os.path.join(DATA_DIR, 'goa_human_complex.gaf.gz')

GO_HUMAN_ISOFORM_ANNOTATIONS_URL = 'http://geneontology.org/gene-associations/goa_human_isoform.gaf.gz'
GO_HUMAN_ISOFORM_ANNOTATIONS_PATH = os.path.join(DATA_DIR, 'goa_human_isoform.gaf.gz')

GO_HUMAN_RNA_ANNOTATIONS_URL = 'http://geneontology.org/gene-associations/goa_human_rna.gaf.gz'
GO_HUMAN_RNA_ANNOTATIONS_PATH = os.path.join(DATA_DIR, 'goa_human_rna.gaf.gz')

#: GAF columns, see: http://geneontology.org/docs/go-annotation-file-gaf-format-2.1/
GAF_COLUMNS = [
    'db',
    'db_id',
    'db_symbol',
    'qualifier',
    'go_id',
    'provenance',  # pubmed curies, go curies, etc.
    'evidence_code',
    'modifications',  # with/from. TODO
    'aspect',  # P (biological process), F (molecular function), or C (cellular component)
    'db_label',
    'db_synonym',
    'db_type',
    'taxonomy_id',  # as a CURIE
    'date',  # date of annotation
    'assigned_by',
    'annotation_extensions',  #
    'gene_product_id',
]
