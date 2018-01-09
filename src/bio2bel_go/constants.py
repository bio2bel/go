# -*- coding: utf-8 -*-

import os

from bio2bel.utils import get_connection, get_data_dir

MODULE_NAME = 'go'
DATA_DIR = get_data_dir(MODULE_NAME)
DEFAULT_CACHE_CONNECTION = get_connection(MODULE_NAME)

#: The web location of the GO OBO file
GO_OBO_URL = 'http://purl.obolibrary.org/obo/go/go-basic.obo'
#: The local cache location where the GO OBO file is stored
GO_OBO_FILE = os.path.join(DATA_DIR, 'go-basic.obo')
