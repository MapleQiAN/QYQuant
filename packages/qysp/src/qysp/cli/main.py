"""QYS CLI — QYQuant Strategy Protocol 命令行工具。"""

import click

from qysp import __version__


@click.group()
@click.version_option(version=__version__, prog_name="qys")
def cli() -> None:
    """QYS — QYQuant Strategy Protocol CLI."""


if __name__ == "__main__":
    cli()
