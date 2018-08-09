# -*- coding: utf-8 -*-

"""BEL DSL elements for GO."""

from pybel.dsl import bioprocess, named_complex_abundance

from .constants import MODULE_NAME

GO = MODULE_NAME.upper()


def gocc(name, identifier) -> named_complex_abundance:
    """Make a GO complex node."""
    return named_complex_abundance(
        namespace=GO,
        name=name,
        identifier=identifier,
    )


def gobp(name, identifier) -> bioprocess:
    """Make a GO biological process node."""
    return bioprocess(
        namespace=GO,
        name=name,
        identifier=identifier
    )
