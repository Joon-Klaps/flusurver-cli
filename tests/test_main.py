import unittest
from click.testing import CliRunner
from src.main import cli
import tempfile
import os
import responses  # Add this to mock HTTP requests

class TestMain(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        # Create a temporary sequence file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.temp_file.write('>HA_H1N1_Human_2009_Norway3206-3 gi|269978854|gb|ACZ56080.1| hemagglutinin [Influenza A virus (A/Norway/3206-3/2009(H1N1))]\nMKAILVVLLYTFATANADTLCIGYHANNSTDTVDTVLEKNVTVTHSVNLLEDKHNGKLCKLRGVAPLHLGKCNIAGWILGNPECESLSTASSWSYIVETSSSDNGTCYPGDFIDYEELREQLSSVSSFERFEIFPKTSSWPNHDSNKGVTAACSHAGAKSFYKNLIWLVKKGNSYPKLSKSYINDKGKEVLVLWGIHHPSTSADQQSLYQNADAYVFVGTSRYSKKFKPEIAIRPKVRGQEGRMNYYWTLVEPGDKITFEATGNLVVPRYAFAMERNAGSGIIISDTPVHDCNTTCQTPKGAINTSLPFQNIHPITIGKCPKYVKSTKLRLATGLRNVPSIQSRGLFGAIAGFIEGGWTGMVDGWYGYHHQNEQGSGYAADLKSTQNAIDEITNKVNSVIEKMNTQFTAVGKEFNHLEKRIENLNKKVDDGFLDIWTYNAELLVLLENERTLDYHDSNVKNLYEKVRSQLKNNAKEIGNGCFEFYHKCDNTCMESVKNGTYDYPKYSEEAKLNREEIDGVKLESTRIYQILAIYSTVASSLVLVVSLGAISFWMCSNGSLQCRICI')
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    @responses.activate
    def test_submit_command(self):
        # Mock the HTTP response
        responses.add(
            responses.POST,
            "https://flusurver.bii.a-star.edu.sg/cgi-bin/flumapBlast3.pl",
            json={"status": "success"},
            status=200
        )

        result = self.runner.invoke(cli, ['submit',
                                        '--seqfile', self.temp_file.name,
                                        '--forceref', 'test',
                                        '--lclq', '1'])
        self.assertEqual(result.exit_code, 0)

    def test_submit_command_file_not_found(self):
        result = self.runner.invoke(cli, ['submit',
                                        '--seqfile', 'nonexistent.fasta',
                                        '--forceref', 'test',
                                        '--lclq', '1'])
        self.assertNotEqual(result.exit_code, 0)

if __name__ == '__main__':
    unittest.main()