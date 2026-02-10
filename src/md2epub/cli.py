
import click
import os

@click.group()
def main():
    """md2epub CLI: Convert Markdown to EPUB."""
    pass

@main.command()
@click.argument('output_dir', type=click.Path(), required=False, default='.')
def init(output_dir):
    """Initialize a new Markdown book directory using Cookiecutter."""
    click.echo(f"Initializing book in {output_dir}")
    try:
        from cookiecutter.main import cookiecutter
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'cookiecutter-book')
        cookiecutter(
            template_path,
            output_dir=output_dir 
        )
        click.echo("Book structure created successfully.")
    except Exception as e:
        click.echo(f"Error initializing book: {e}", err=True)

@main.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False))
def compile(path):
    """Compile the Markdown book directory into an EPUB file."""
    click.echo(f"Compiling book from {path}")
    try:
        from md2epub.epub_builder import EpubBuilder
        builder = EpubBuilder(path)
        output_file = builder.build()
        click.echo(f"Successfully compiled to {output_file}")
    except Exception as e:
        click.echo(f"Error compiling book: {e}", err=True)

@main.command()
@click.argument('epub_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('output_dir', type=click.Path())
def unpack(epub_path, output_dir):
    """Unpack an EPUB file into a Markdown book directory."""
    click.echo(f"Unpacking {epub_path} into {output_dir}")
    try:
        from md2epub.epub_extractor import EpubExtractor
        extractor = EpubExtractor(epub_path)
        extractor.extract_metadata() # Ensure metadata is ready
        extractor.save_project(output_dir)
        click.echo(f"Successfully unpacked to {output_dir}")
    except Exception as e:
        click.echo(f"Error unpacking book: {e}", err=True)

if __name__ == "__main__":
    main()
