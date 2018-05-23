# -*- coding: utf-8 -*-

import logging
import networkx as nx

from bio2bel_go.parser import get_go
from pybel.constants import NAMESPACE_DOMAIN_BIOPROCESS, belns_encodings
from pybel.resources.definitions import write_namespace

__all__ = [
    'write_belns',
]

log = logging.getLogger(__name__)

_def_encoding = ''.join(sorted(belns_encodings.keys()))


def get_values(go_network):
    rv = {}

    for node, data in go_network.nodes_iter(data=True):
        name = data.get('name')

        if name is None:
            log.warning('missing name: %s', node)
            continue

        namespace = data['namespace']

        if namespace == 'biological_process':
            encoding = 'BO'
        elif 'GO:0032991' in nx.descendants(go_network, node):  # GO:0032991 is "macromolecular complex"
            encoding = "C"
        else:
            encoding = _def_encoding

        rv[name] = encoding

    return rv


def write_belns(*, path=None, file=None):
    """Writes the GO namespace

    .. todo:: add a mapping for molecular function, process, cell component, etc

    :param Optional[str] path:
    :param file file: A write-enabled file or file-like. Defaults to standard out.
    """
    n = get_go(path=path)
    values = get_values(n)

    write_namespace(
        namespace_name='Gene Ontology',
        namespace_keyword='GO',
        namespace_domain=NAMESPACE_DOMAIN_BIOPROCESS,
        author_name='Charles Tapley Hoyt',
        author_copyright='CC by 4.0',
        citation_name='Gene Ontology',
        values=values,
        file=file
    )


if __name__ == '__main__':
    import os

    logging.basicConfig(level=logging.DEBUG)
    log.setLevel(logging.DEBUG)

    log.info('writing to desktop')
    with open(os.path.expanduser('~/Desktop/go.belns'), 'w') as f:
        write_belns(file=f)
