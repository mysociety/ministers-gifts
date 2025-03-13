import rich_click as click

from .download import download_and_store


@click.group()
def cli():
    pass


def main():
    cli()


@cli.command()
def download():
    download_and_store()


if __name__ == "__main__":
    main()
