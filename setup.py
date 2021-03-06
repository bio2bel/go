# -*- coding: utf-8 -*-

"""Setup module for Bio2BEL GO."""

import codecs
import os
import re

import setuptools

PACKAGES = setuptools.find_packages(where='src')
KEYWORDS = ['Biological Expression Language', 'BEL', 'Systems Biology', 'Networks Biology', 'Gene Ontology']
META_PATH = os.path.join('src', 'bio2bel_go', '__init__.py')
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.6',
    'Topic :: Scientific/Engineering :: Bio-Informatics'
]
INSTALL_REQUIRES = [
    'networkx>=2.1',
    'pybel>=0.13.0,<0.14.0',
    'obonet',
    'click',
    'bio2bel>=0.1.3',
    'tqdm',
    'sqlalchemy',
]
ENTRY_POINTS = {
    'bio2bel': [
        'go = bio2bel_go',
    ],
    'console_scripts': [
        'bio2bel_go = bio2bel_go.cli:main',
    ]
}

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Build an absolute path from *parts* and return the contents of the resulting file. Assume UTF-8 encoding."""
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """Extract __*meta*__ from META_FILE."""
    meta_match = re.search(
        r'^__{meta}__ = ["\']([^"\']*)["\']'.format(meta=meta),
        META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError('Unable to find __{meta}__ string'.format(meta=meta))


def get_long_description():
    """Get the long_description from the README.rst file. Assume UTF-8 encoding."""
    with codecs.open(os.path.join(HERE, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
    return long_description


if __name__ == '__main__':
    setuptools.setup(
        name=find_meta('title'),
        version=find_meta('version'),
        description=find_meta('description'),
        long_description=get_long_description(),
        url=find_meta('url'),
        author=find_meta('author'),
        author_email=find_meta('email'),
        maintainer=find_meta('author'),
        maintainer_email=find_meta('email'),
        license=find_meta('license'),
        packages=PACKAGES,
        package_dir={'': 'src'},
        install_requires=INSTALL_REQUIRES,
        entry_points=ENTRY_POINTS,
        classifiers=CLASSIFIERS,
        keywords=KEYWORDS,
        zip_safe=False,
    )
