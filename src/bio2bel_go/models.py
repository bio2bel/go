# -*- coding: utf-8 -*-

"""SQLAlchemy models for Bio2BEL GO."""

from __future__ import annotations

from typing import List, Mapping, Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import backref, relationship

from bio2bel.manager.compath import CompathPathwayMixin, CompathProteinMixin
from pybel import BELGraph
from pybel.dsl import Abundance, BaseEntity, BiologicalProcess, NamedComplexAbundance
from .constants import GO_BIOLOGICAL_PROCESS, GO_CELLULAR_COMPONENT, GO_MOLECULAR_FUNCTION, MODULE_NAME

TERM_TABLE_NAME = f'{MODULE_NAME}_term'
TARGET_TABLE_NAME = f'{MODULE_NAME}_target'
SYNONYM_TABLE_NAME = f'{MODULE_NAME}_synonym'
HIERARCHY_TABLE_NAME = f'{MODULE_NAME}_hierarchy'
ANNOTATION_TABLE_NAME = f'{MODULE_NAME}_annotation'

Base: DeclarativeMeta = declarative_base()


class Term(Base, CompathPathwayMixin):
    """Represents a Gene Ontology term."""

    __tablename__ = TERM_TABLE_NAME

    id = Column(Integer, primary_key=True)

    prefix = MODULE_NAME
    identifier = Column(String(32), unique=True, nullable=False, index=True, doc='GO Identifier')
    name = Column(String(255), unique=True, nullable=False, index=True)

    namespace = Column(String(255), nullable=True)
    definition = Column(Text)
    is_complex = Column(Boolean, default=False, nullable=False,
                        doc='Cache if is descendant of GO:0032991 "macromolecular complex"')

    annotations: List[Annotation]

    def to_json(self) -> Mapping[str, str]:
        """Make a summary dictionary for the term."""
        return dict(
            name=self.name,
            namespace=self.namespace,
            definition=self.definition,
            go_id=self.identifier,
        )

    @property
    def bel_encoding(self) -> Optional[str]:
        """Get the BEL encoding for this term."""
        if self.namespace == GO_BIOLOGICAL_PROCESS:
            return 'B'

        if self.namespace == GO_CELLULAR_COMPONENT:
            if self.is_complex:
                return 'C'
            else:
                return 'A'

        if self.namespace == GO_MOLECULAR_FUNCTION:
            return 'Y'

    @property
    def proteins(self) -> List[Target]:
        """Get the proteins for the GO term."""
        return [annotation.target for annotation in self.annotations]

    def to_pybel(self) -> Optional[BaseEntity]:
        """Convert this term to a BEL node."""
        if self.namespace == 'biological_process':
            return BiologicalProcess(
                namespace=MODULE_NAME,
                name=self.name,
                identifier=self.identifier,
            )

        if self.namespace == 'cellular_component':
            if self.is_complex:
                return NamedComplexAbundance(
                    namespace=MODULE_NAME,
                    name=self.name,
                    identifier=self.identifier,
                )
            else:
                return Abundance(
                    namespace=MODULE_NAME,
                    name=self.name,
                    identifier=self.identifier,
                )


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

    subject_id = Column(Integer, ForeignKey(f'{Term.__tablename__}.id'), nullable=False)
    subject = relationship(Term, foreign_keys=[subject_id],
                           backref=backref('out_edges', lazy='dynamic', cascade='all, delete-orphan'))

    relation = Column(String(32), nullable=True, index=True)

    object_id = Column(Integer, ForeignKey(f'{Term.__tablename__}.id'), nullable=False)
    object = relationship(Term, foreign_keys=[object_id],
                          backref=backref('in_edges', lazy='dynamic', cascade='all, delete-orphan'))

    def add_to_graph(self, graph: BELGraph) -> Optional[str]:
        """Add this hierarchical relation to the graph."""
        sub = self.subject.to_pybel()
        obj = self.object.to_pybel()

        if not sub or not obj:
            return

        return graph.add_is_a(sub, obj)


class Target(Base, CompathProteinMixin):
    """Represent a target."""

    __tablename__ = TARGET_TABLE_NAME
    id = Column(Integer, primary_key=True)

    db = Column(String, nullable=False)
    db_id = Column(String, nullable=False)
    db_symbol = Column(String, nullable=False)
    hgnc_id = Column(String, nullable=True)
    hgnc_symbol = Column(String, nullable=True)

    taxonomy_id = Column(String, nullable=False)

    def __repr__(self) -> str:
        return f'{self.db}:{self.db_id} ! {self.db_symbol}'

    def to_pybel(self) -> Optional[BaseEntity]:
        """Get BEL thing."""
        if self.db == 'ComplexPortal':
            return NamedComplexAbundance(
                namespace='complexportal',
                name=self.db_symbol,
                identifier=self.db_id,
            )


class Annotation(Base):
    """Represents a GO annotation."""

    __tablename__ = ANNOTATION_TABLE_NAME
    id = Column(Integer, primary_key=True)

    term_id = Column(Integer, ForeignKey(f'{Term.__tablename__}.id'), nullable=False)
    term = relationship(Term, backref=backref('annotations', lazy='dynamic'))

    target_id = Column(Integer, ForeignKey(f'{Target.__tablename__}.id'), nullable=False)
    target = relationship(Target, backref=backref('annotations', lazy='dynamic'))

    qualifier = Column(String, nullable=True)
    provenance_db = Column(String, nullable=True)
    provenance_id = Column(String, nullable=True)
    evidence_code = Column(String, nullable=False)

    def _get_citation(self):
        if self.provenance_db == 'pmid':
            return self.evidence_code
        else:
            return {'type': self.provenance_db, 'reference': self.provenance_id}

    def add_to_graph(self, graph: BELGraph) -> Optional[str]:
        """Add this annotation to the BEL graph."""
        source = self.term.to_pybel()
        target = self.target.to_pybel()

        if not source or not target:
            return

        return graph.add_association(
            source,
            target,
            evidence=self.evidence_code,
            citation=self._get_citation(),
            annotations={
                'Species': self.target.taxonomy_id,
            }
        )
