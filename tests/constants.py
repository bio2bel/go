# -*- coding: utf-8 -*-

"""Testing constants for Bio2BEL GO."""

from bio2bel.testing import AbstractTemporaryCacheClassMixin

from bio2bel_go import Manager

__all__ = [
    'TemporaryCacheClass',
]


class TemporaryCacheClass(AbstractTemporaryCacheClassMixin):
    """A test case containing a temporary database and a Bio2BEL GO manager."""

    Manager = Manager
