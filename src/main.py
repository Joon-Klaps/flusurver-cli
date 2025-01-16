import click
import requests

@click.group()
def cli():
    """CLI tool for interacting with flu sequences and GISAID data."""
    pass

@cli.command()
@click.option('--seqfile', '-f', type=click.Path(exists=True), required=True,
              help='Path to sequence file')
@click.option('--forceref', '-r', default='autorefall',
              help='Force reference option (default: autorefall)')
@click.option('--lclq', '-l', default=1, type=int,
              help='Local quality setting (default: 1)')
def submit(seqfile, forceref, lclq):
    """Submit sequence data for analysis."""
    url = "https://flusurver.bii.a-star.edu.sg/cgi-bin/flumapBlast3.pl"

    try:
        with open(seqfile, 'r') as f:
            sequence_data = f.read().strip()
    except IOError as e:
        click.echo(f"Error reading file: {e}", err=True)
        return

    form_data = {
        'seq': sequence_data,
        'forceref': forceref,
        'lclq': str(lclq),
        'Submit': 'Submit'
    }

    files = {
        'seqfile': (seqfile, open(seqfile, 'rb'))
    }

    try:
        response = requests.post(url, data=form_data, files=files)
        response.raise_for_status()
        click.echo(f"Status Code: {response.status_code}")
        click.echo(f"Response Text: {response.text}")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error making request: {e}", err=True)
    finally:
        files['seqfile'][1].close()

if __name__ == '__main__':
    cli()
