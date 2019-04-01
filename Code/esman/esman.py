import click
from Common import *

@click.group()
def general():
    pass

@general.command()
def extractSubset():
    pass

@general.command()
def installDeps():
    timestampPrint('Installing dependencies')
    pass