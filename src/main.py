import rich_click as click
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import csv
from pathlib import Path
import re

class HTMLResponse:
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.base_url = "https://flusurver.bii.a-star.edu.sg"
        self.report_links = self._parse_report_links()

    def _parse_report_links(self):
        links = {}
        descriptions = {
            'mutation_report': 'detailed mutation report',
            'query_summary': 'query summary report',
            'clade_call': 'query to clade call',
            'drug_sensitivity': 'drug sensitivity summary report'
        }

        for a in self.soup.find_all('a', href=True):
            href = a.get('href', '')
            if any(ext in href for ext in ['.txt', '.csv', '.tsv']):
                for key, desc in descriptions.items():
                    if desc.lower() in str(a.parent).lower():
                        # Clean up the href path
                        clean_href = re.sub(r'^\.\./?', '', href)
                        links[key] = {
                            'url': f"{self.base_url}/{clean_href}",
                            'description': desc
                        }

        # Check for missing reports
        missing_reports = set(descriptions.keys()) - set(links.keys())
        if missing_reports:
            click.secho(f"✗ Warning: Missing reports: {', '.join(missing_reports)}", fg='yellow', bold=True)
        return links

    def download_reports(self, output_dir: Path):
        results = {}
        for report_type, link_info in self.report_links.items():
            try:
                response = requests.get(link_info['url'])
                response.raise_for_status()

                # Create output filename based on report type
                output_file = output_dir / f"{report_type}.{link_info['url'].split('.')[-1]}"
                output_file.write_text(response.text)
                results[report_type] = {'success': True, 'path': output_file}

            except requests.exceptions.RequestException:
                results[report_type] = {
                    'success': False,
                    'url': link_info['url'],
                    'description': link_info['description']
                }

        return results

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
@click.option('--debug', '-d', default=False, is_flag=True,  type=bool,
                help='Enable debug mode')
@click.option('--output-dir', '-o', type=click.Path(), default='reports',
              help='Output directory for reports (default: reports)')
def submit(seqfile, forceref, lclq, debug, output_dir):
    """Submit sequence data for analysis and save results."""
    url = "https://flusurver.bii.a-star.edu.sg/cgi-bin/flumapBlast3.pl"
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    try:
        with open(seqfile, 'r') as f:
            sequence_data = f.read().strip()

        # Count sequences
        sequence_count = sequence_data.count('>')
        click.echo(f"Found {sequence_count} sequence{'s' if sequence_count != 1 else ''} in input file")

        form_data = {
            'seq': sequence_data,
            'forceref': forceref,
            'lclq': str(lclq),
            'Submit': 'Submit'
        }

        files = {
            'seqfile': (seqfile, open(seqfile, 'rb'))
        }

        click.echo(f"Sending request to {url}...")
        click.echo("Request parameters:")
        click.echo(f"  Force reference: {forceref}")
        click.echo(f"  Local quality: {lclq}")

        try:
            response = requests.post(url, data=form_data, files=files)
            response.raise_for_status()
            click.echo("Request successful!")

            # Parse response and save results
            html_response = HTMLResponse(response.text)
            if debug:
                open(output_dir / 'response.html', 'w').write(response.text)

            # Download and save report files
            results = html_response.download_reports(output_dir)
            if debug:
                click.echo(results)

            click.echo("\nResults:")
            for report_type, result in results.items():
                if result['success']:
                    click.secho(f"✓ {report_type}: Saved to {result['path']}", fg='green')
                else:
                    click.secho(f"✗ {report_type}: Could not download. Available at:", fg='red')
                    click.secho(f"  URL: {result['url']}", fg='red')
                    click.secho(f"  Description: {result['description']}", fg='red')

        except requests.exceptions.RequestException as e:
            click.echo(f"Error making request: {e}", err=True)
    except IOError as e:
        click.echo(f"Error reading file: {e}", err=True)
    finally:
        if 'files' in locals() and 'seqfile' in files:
            files['seqfile'][1].close()

if __name__ == '__main__':
    cli()
