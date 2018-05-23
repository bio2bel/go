# -*- coding: utf-8 -*-

"""SQLAlchemy models for Bio2BEL GO."""

from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

from pybel.dsl import BaseEntity
from .constants import MODULE_NAME
from .dsl import gobp, gocc

TERM_TABLE_NAME = f'{MODULE_NAME}_term'
SYNONYM_TABLE_NAME = f'{MODULE_NAME}_synonym'
HIERARCHY_TABLE_NAME = f'{MODULE_NAME}_hierarchy'

Base = declarative_base()

_GO_NAMESPACE = MODULE_NAME.upper()


class Term(Base):
    """Represents a Gene Ontology term."""

    __tablename__ = TERM_TABLE_NAME

    id = Column(Integer, primary_key=True)

    go_id = Column(String(32), unique=True, nullable=False, index=True, doc='GO Identifier')
    name = Column(String(255), unique=True, nullable=False, index=True)
    namespace = Column(String(255), nullable=False, index=True)
    definition = Column(Text)
    is_complex = Column(Boolean, default=False, nullable=False,
                        doc='Cache if is descendant of GO:0032991 "macromolecular complex"')

    def __repr__(self):
        return self.name

    def as_bel(self) -> Optional[BaseEntity]:
        """Convert this term to a BEL node."""

        if self.namespace == 'biological_process':
            return gobp(name=self.name, identifier=self.go_id)

        if self.namespace == 'cellular_component' and self.is_complex:
            return gocc(name=self.name, identifier=self.go_id)


class Synonym(Base):
    """Represents a synonym of a Gene Ontology term."""

    __tablename__ = SYNONYM_TABLE_NAME

    id = Column(Integer, primary_key=True)

    name = Column(String(1023), nullable=False, index=True)

    term_id = Column(Integer, ForeignKey(f'{TERM_TABLE_NAME}.id'), nullable=False)
    term = relationship(Term, backref=backref('synonyms'))

    def __repr__(self):
        return self.name


class Hierarchy(Base):
    """Represents the GO hierarchy."""
    __tablename__ = HIERARCHY_TABLE_NAME

    id = Column(Integer, primary_key=True)

    subject_id = Column(Integer, ForeignKey(f'{TERM_TABLE_NAME}.id'), nullable=False)
    subject = relationship(Term, foreign_keys=[subject_id],
                           backref=backref('out_edges', lazy='dynamic', cascade='all, delete-orphan'))

    relation = Column(String(32), nullable=True, index=True)

    object_id = Column(Integer, ForeignKey(f'{TERM_TABLE_NAME}.id'), nullable=False)
    object = relationship(Term, foreign_keys=[object_id],
                          backref=backref('in_edges', lazy='dynamic', cascade='all, delete-orphan'))
