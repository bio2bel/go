# -*- coding: utf-8 -*-

import sys

import click

from bio2bel_go.to_belns import write_belns


@click.group()
def main():
    """GO to BEL"""


@main.command()
@click.option('-o', '--output', default=sys.stdout)
@click.option('-p', '--path')
def write(output, path):
    """Populate the database"""
    write_belns(path=path, file=output)


if __name__ == '__main__':
    main()
