import unittest
import tempfile
import os
from gimmemotifs.scanner import *
from gimmemotifs.fasta import Fasta
from time import sleep

class TestScanner(unittest.TestCase):
    """ A test class to test scanner funcitonalitu """

    def setUp(self):
        self.data_dir = "test/data/scanner"
        
        self.motifs = os.path.join(self.data_dir, "motif.pwm")
        self.fa = os.path.join(self.data_dir, "test.fa")

    def test1_scan_sequences(self):
        """ Scanner """
        for ncpus in [1,2,3]:
            s = Scanner(ncpus=ncpus)
            s.set_motifs(self.motifs)
        
            f = Fasta(self.fa)
            
            s.set_threshold(threshold=0.0)
            nmatches = [len(m[0]) for m in s._scan_sequences(f.seqs, 1, False)]
            self.assertEqual([1,1,1], nmatches)

            s.set_threshold(threshold=0.99)
            nmatches = [len(m[0]) for m in s._scan_sequences(f.seqs, 1, False)]
            self.assertEqual([0,1,1], nmatches)
        
            s.set_threshold(threshold=0.99)
            nmatches = [len(m[0]) for m in s._scan_sequences(f.seqs, 10, False)]
            self.assertEqual([0,1,2], nmatches)

            s.set_threshold(threshold=0.99)
            nmatches = [len(m[0]) for m in s._scan_sequences(f.seqs, 10, True)]
            self.assertEqual([0,2,4], nmatches)

    def test2_scan_fasta_to_best_match(self):
        result =  scan_fasta_to_best_match(self.fa, self.motifs)
        
        scores = [-20.08487, 9.029220, 9.029220]

        self.assertIn("AP1", result)
        
        for score,match in zip(scores, result["AP1"]):
            self.assertAlmostEqual(score, match[0], 5)

    def test3_scan_fasta_to_best_score(self):
        result = scan_fasta_to_best_score(self.fa, self.motifs)
        
        scores = [-20.08487, 9.029220, 9.029220]

        self.assertIn("AP1", result)
        for score,match in zip(scores, result["AP1"]):
            self.assertAlmostEqual(score, match, 5)

    def testThreshold(self):
        s = Scanner()
        s.set_motifs("test/data/pwms/motifs.pwm")
        
        fname = "test/data/scan/scan_test_regions.fa"
        s.set_threshold(fdr=0.02, filename=fname)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
