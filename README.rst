Bio2BEL GO |build| |coverage| |documentation| |zenodo|
======================================================
Converts the Gene Ontology (GO) to BEL

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
``bio2bel_go`` can be installed easily from `PyPI <https://pypi.python.org/pypi/bio2bel_go>`_ with
the following code in your favorite terminal:

.. code-block:: sh

    $ python3 -m pip install bio2bel_go

or from the latest code on `GitHub <https://github.com/bio2bel/go>`_ with:

.. code-block:: sh

    $ python3 -m pip install git+https://github.com/bio2bel/go.git@master

Setup
-----
GO can be downloaded and populated from either the Python REPL or the automatically installed command line
utility.

Python REPL
~~~~~~~~~~~
.. code-block:: python

    >>> import bio2bel_go
    >>> go_manager = bio2bel_go.Manager()
    >>> go_manager.populate()

Command Line Utility
~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash

    bio2bel_go populate

Citation
--------
- Ashburner, M., *et al.* (2000). `Gene ontology: tool for the unification of biology <https://doi.org/10.1038/75556>`_.
  The Gene Ontology Consortium. Nature Genetics, 25(1), 25–9.

Links
-----
- http://geneontology.org/page/ontology-documentation

.. |build| image:: https://travis-ci.org/bio2bel/go.svg?branch=master
    :target: https://travis-ci.org/bio2bel/go
    :alt: Build Status

.. |documentation| image:: http://readthedocs.org/projects/bio2bel-go/badge/?version=latest
    :target: http://bio2bel.readthedocs.io/projects/go/en/latest/?badge=latest
    :alt: Documentation Status

.. |pypi_version| image:: https://img.shields.io/pypi/v/bio2bel_go.svg
    :alt: Current version on PyPI

.. |coverage| image:: https://codecov.io/gh/bio2bel/go/coverage.svg?branch=master
    :target: https://codecov.io/gh/bio2bel/go?branch=master
    :alt: Coverage Status

.. |climate| image:: https://codeclimate.com/github/bio2bel/go/badges/gpa.svg
    :target: https://codeclimate.com/github/bio2bel/go
    :alt: Code Climate

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/bio2bel_go.svg
    :alt: Stable Supported Python Versions

.. |pypi_license| image:: https://img.shields.io/pypi/l/bio2bel_go.svg
    :alt: MIT License

.. |zenodo| image:: https://zenodo.org/badge/99944678.svg
   :target: https://zenodo.org/badge/latestdoi/99944678
