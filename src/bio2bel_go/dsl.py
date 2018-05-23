# -*- coding: utf-8 -*-

"""BEL DSL elements for GO."""

from pybel.dsl import bioprocess, complex_abundance
from .constants import MODULE_NAME

GO = MODULE_NAME.upper()


def gocc(name, identifier):
    """Makes a GO complex node

    :rtype: complex_abundance
    """
    return complex_abundance(
        namespace=GO,
        name=name,
        identifier=identifier,
        members=[]
    )


def gobp(name, identifier):
    """Makes a GO biological process node

    :rtype: bioprocess
    """
    return bioprocess(
        namespace=GO,
        name=name,
        identifier=identifier
    )
