# -*- coding: utf-8 -*-

"""BEL DSL elements for GO."""

from pybel.dsl import bioprocess


def gobp(name, identifier) -> bioprocess:
    """Make a GO biological process node."""
    return bioprocess(
        namespace='go',
        name=name,
        identifier=identifier
    )
