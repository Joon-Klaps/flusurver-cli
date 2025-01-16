import click
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import csv
from pathlib import Path

@dataclass
class Mutation:
    name: str
    color: str
    protein: str
    structure_link: Optional[str] = None

class HTMLResponse:
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.mutations = self._parse_mutations()
        self.drug_warnings = self._parse_drug_sensitivity()

    def _parse_mutations(self) -> List[Mutation]:
        mutations = []
        for link in self.soup.find_all('a', href=True):
            if 'javascript:' in link.get('href', ''):
                font_tag = link.find('font')
                if font_tag and font_tag.b:
                    color = font_tag.get('color', '')
                    mutation_text = font_tag.b.text
                    protein = mutation_text.split('_')[0] if '_' in mutation_text else mutation_text[:2]

                    parent_td = link.find_parent('td')
                    structure_link = None
                    if parent_td:
                        next_a = parent_td.find('a', string='show in structure')
                        if next_a and 'onClick' in next_a.attrs:
                            structure_link = next_a['onClick']

                    mutations.append(Mutation(
                        name=mutation_text,
                        color=color,
                        protein=protein,
                        structure_link=structure_link
                    ))
        return mutations

    def _parse_drug_sensitivity(self) -> List[str]:
        warnings = []
        for font in self.soup.find_all('font', color='red'):
            if "Reduced sensitivity or resistance" in font.text:
                warnings.append(font.text.strip())
        return warnings

    def to_tsv(self, output_path: Path):
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['Protein', 'Mutation', 'Effect', 'Structure Link', 'Drug Warning'])

            for mutation in self.mutations:
                writer.writerow([
                    mutation.protein,
                    mutation.name,
                    mutation.color,
                    mutation.structure_link or 'N/A',
                    '; '.join(self.drug_warnings) if mutation.color == 'red' else 'N/A'
                ])

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
@click.option('--output', '-o', type=click.Path(), default='mutations.tsv',
              help='Output TSV file path (default: mutations.tsv)')
def submit(seqfile, forceref, lclq, output):
    """Submit sequence data for analysis and save results."""
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

        # Parse response and save results
        html_response = HTMLResponse(response.text)
        output_path = Path(output)
        html_response.to_tsv(output_path)

        click.echo(f"Analysis complete. Results saved to {output_path}")

        # Print summary
        for mutation in html_response.mutations:
            color = {
                'red': 'HIGH RISK',
                'orange': 'MEDIUM RISK',
                'green': 'LOW RISK'
            }.get(mutation.color, 'UNKNOWN')

            click.echo(f"{mutation.name}: {color}")

        if html_response.drug_warnings:
            click.echo("\nWARNINGS:")
            for warning in html_response.drug_warnings:
                click.echo(click.style(warning, fg="red"))

    except requests.exceptions.RequestException as e:
        click.echo(f"Error making request: {e}", err=True)
    finally:
        files['seqfile'][1].close()

if __name__ == '__main__':
    cli()
