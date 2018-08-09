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
