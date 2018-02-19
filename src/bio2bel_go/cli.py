# -*- coding: utf-8 -*-

import logging
import sys

import click

import pybel
from bio2bel_go.enrich import upload_bel
from bio2bel_go.manager import Manager
from bio2bel_go.to_belns import write_belns


@click.group()
def main():
    """GO to BEL"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@main.command()
def summarize():
    """Summarize the contents of the graph"""
    m = Manager()
    for k, v in m.summarize().items():
        click.echo('{}: {}'.format(k.capitalize(), v))


@main.command()
@click.option('-o', '--output', type=click.File('w'), default=sys.stdout)
@click.option('-p', '--path')
def write(output, path):
    """Populate the database"""
    write_belns(path=path, file=output)


@main.command()
@click.option('-o', '--output', type=click.File('w'), default=sys.stdout)
@click.option('-p', '--path')
def write_bel(output, path):
    """Writes GO as a BEL script"""
    m = Manager()
    m.populate(path=path)
    graph = m.to_bel()
    pybel.to_bel(graph, output)


@main.command()
def store():
    """Store GO BEL Graph to PyBEL edge store"""
    upload_bel()


if __name__ == '__main__':
    main()
