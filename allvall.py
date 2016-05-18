# -*- coding: utf-8 -*-
"""
Created on Tue May 17 12:28:59 2016

@author: kp14
"""
import itertools
import glob
import os
import subprocess
import sys


CMD = '{prog} {seq1} {seq2} stdout -gapopen 10.0 -gapextend 0.5 >> {prog}_alignments.txt'
PROGS = ['water', 'needle']


def run(path):
    files = glob.glob(os.path.join(path, '*.fasta'))
    for combi in itertools.combinations(files, 2):
        for prog in PROGS:
            subprocess.call(CMD.format(prog=prog,
                                       seq1=combi[0],
                                       seq2=combi[1]), shell=True)


if __name__ == "__main__":
    path = sys.argv[1]
    run(path)