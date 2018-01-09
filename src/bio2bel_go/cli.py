# -*- coding: utf-8 -*-

import logging
import sys

import click

from bio2bel_go.enrich import upload_bel
from bio2bel_go.to_belns import write_belns


@click.group()
def main():
    """GO to BEL"""
    logging.basicConfig(level=logging.DEBUG)


@main.command()
@click.option('-o', '--output', default=sys.stdout)
@click.option('-p', '--path')
def write(output, path):
    """Populate the database"""
    write_belns(path=path, file=output)


@main.command()
def store():
    """Store GO BEL Graph to PyBEL edge store"""
    upload_bel()


if __name__ == '__main__':
    main()
