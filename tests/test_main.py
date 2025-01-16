import unittest
from click.testing import CliRunner
from pathlib import Path
import responses
from src.main import cli

class TestMain(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = Path(__file__).parent
        self.data_dir = self.test_dir / 'data'
        self.sequence_file = self.data_dir / 'sequence.fa'
        self.output_file = self.data_dir / 'output.tsv'
        self.data_dir.mkdir(exist_ok=True)
        self.responses = responses.RequestsMock(assert_all_requests_are_fired=False)
        self.responses.start()

    def tearDown(self):
        if self.output_file.exists():
            self.output_file.unlink()
        self.responses.stop()
        self.responses.reset()

    @responses.activate
    def test_submit_command_with_sample_data(self):
        # Mock the FluSurver response
        with open(self.test_dir / 'data/response.html', 'r') as f:
            mock_response = f.read()

        self.responses.add(
            responses.POST,
            "https://flusurver.bii.a-star.edu.sg/cgi-bin/flumapBlast3.pl",
            body=mock_response,
            status=200
        )

        result = self.runner.invoke(cli, [
            'submit',
            '--seqfile', str(self.sequence_file),
            '--forceref', 'test',
            '--lclq', '1',
            '--output', str(self.output_file)
        ])

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(self.output_file.exists())

        with open(self.output_file, 'r') as f:
            content = f.read()
            self.assertIn('Protein', content)
            self.assertIn('Mutation', content)
            self.assertIn('Effect', content)

    def test_submit_command_file_not_found(self):
        result = self.runner.invoke(cli, [
            'submit',
            '--seqfile', 'nonexistent.fasta',
            '--forceref', 'test',
            '--lclq', '1',
            '--output', str(self.output_file)
        ])
        self.assertNotEqual(result.exit_code, 0)

if __name__ == '__main__':
    unittest.main()