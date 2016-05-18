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
    with open('water_alignments.txt', 'r', encoding='ascii') as wres, open('test.svg', 'w', encoding='ascii') as svg:
        aln = None
        alignments = []
        for line in wres:
            if line.startswith('# Program:'):
                aln = {}
            elif line.startswith('# 1'):
                seq1 = line.strip().split(':')[1]
            elif line.startswith('# 2'):
                seq2 = line.strip().split(':')[1]
            elif line.startswith('# Identity'):
                identity = line.strip()[23:-2]
            elif line.startswith('# Similarity'):
                similarity = line.strip()[23:-2]
            elif line.startswith('#---'):
                alignments.append(aln)
        for alignment in alignments:
            svg.write('''<svg width="40" height="40">
                         <rect width="40" height="40" style="fill:rgb(0,0,255);stroke-width:3;stroke:rgb(0,0,0)" />
                         </svg> ''')

def _svg_rect(num):
    template = '<rect x="{x}" y="{y}" width="40" height="40" style="fill:rgb(0,0,255);fill-opacity:{opa}" />'





if __name__ == "__main__":
    path = sys.argv[1]
    run(path)