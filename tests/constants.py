# -*- coding: utf-8 -*-

from bio2bel.testing import AbstractTemporaryCacheClassMixin
from bio2bel_go import Manager

__all__ = [
    'TemporaryCacheClass',
]


class TemporaryCacheClass(AbstractTemporaryCacheClassMixin):
    Manager = Manager
