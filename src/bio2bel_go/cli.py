# -*- coding: utf-8 -*-

import sys

import click

import pybel
from bio2bel_go.to_belns import write_belns
from .manager import Manager

main = Manager.get_cli()


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


if __name__ == '__main__':
    main()
