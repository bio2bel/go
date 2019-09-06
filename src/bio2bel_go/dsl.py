# -*- coding: utf-8 -*-

"""BEL DSL elements for GO."""

from pybel.dsl import BiologicalProcess


def gobp(name: str, identifier: str) -> BiologicalProcess:
    """Make a GO biological process node."""
    return BiologicalProcess(
        namespace='go',
        name=name,
        identifier=identifier,
    )
