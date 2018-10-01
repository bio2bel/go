# -*- coding: utf-8 -*-

"""Testing constants for Bio2BEL GO."""

import os

from bio2bel.testing import AbstractTemporaryCacheClassMixin
from bio2bel_go import Manager

__all__ = [
    'TemporaryCacheClass',
]

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_GO_PATH = os.path.join(HERE, 'test_go.obo')


class TemporaryCacheClass(AbstractTemporaryCacheClassMixin):
    """A test case containing a temporary database and a Bio2BEL GO manager."""

    Manager = Manager
    manager: Manager

    @classmethod
    def populate(cls):
        """Populate the database with test data."""
        cls.manager.populate(path=TEST_GO_PATH)
