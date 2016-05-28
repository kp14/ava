# -*- coding: utf-8 -*-
"""
Created on Tue May 17 12:28:59 2016

@author: kp14
"""
import itertools
import glob
import logging
import os
import subprocess
import sys
from collections import defaultdict, namedtuple

logging.basicConfig(level=logging.INFO)

CMD = '{prog} {seq1} {seq2} stdout -gapopen 10.0 -gapextend 0.5 >> {output}'
PROGS = ['water', 'needle']
OUTPUT_FILE_BASE = '{prog}_alignments.txt'
WIDTH = 10
HEIGHT = WIDTH
X_INIT = 95
Y_INIT = 95

Partner = namedtuple('Partner', ['seq', 'identity', 'similarity'])


def run_alignments(path):
    cleanup(path)
    files = glob.glob(os.path.join(path, '*.fasta'))
    files.sort(key=lambda path: _filename_no_ext(path))
    cnt = defaultdict(int)
    alignments_run = 0
    combis_run = 0
    for combi in itertools.combinations_with_replacement(files, 2):
        logging.debug(combi)
        combis_run += 1
        cnt[combi[0]] += 1
        for prog in PROGS:
            alignments_run += 1
            output_file = OUTPUT_FILE_BASE.format(prog=prog)
            subprocess.run(CMD.format(prog=prog,
                                       seq1=combi[0],
                                       seq2=combi[1],
                                       output=output_file), shell=True, cwd=path)
    for fasta, count in cnt.items():
        logging.debug('Alignments run against {fasta}: {count}'.format(fasta=fasta, count=str(count)))
    logging.info('Total number of combinations run: {}'.format(str(combis_run)))
    logging.info('Total number of alignments run: {}'.format(str(alignments_run)))


def visualize_alignments(path):
    for prog in PROGS:
        output_file = OUTPUT_FILE_BASE.format(prog=prog)
        alignments, index = parse_alignment_output(output_file, path)
        generate_svg(alignments, index, path, prog)


def generate_svg(alignments, index, path, prog):
    svg_file = os.path.join(path, '{}_alignments.html'.format(prog))
    with open(svg_file, 'w', encoding='utf8') as svg:
        total = 0
        svg.write('<svg xmlns:svg="http://www.w3.org/2000/svg" width="1000" height="1000">')
        index_dict = {}
        for idx, val in enumerate(index):
            index_dict[val] = idx
        for seq in index:
            svg.write(svg_text_vertical(index_dict, seq))
            svg.write(svg_text_horizontal(index_dict, seq))
            svg.write(svg_guidelines(index_dict, seq))
            for partner in alignments[seq]:
                svg.write(svg_rectangle(index_dict, seq, partner))
                total += 1
        logging.info('Number of <rect> written: {}'.format(str(total)))
        svg.write('</svg>')
    logging.info('Wrote SVG data to: {}'.format(svg_file))


def parse_alignment_output(alignment_file, path):
    with open(os.path.join(path, alignment_file), 'r', encoding='ascii') as wres:
        alignments = defaultdict(list)
        index = set()
        counter = 0
        seq1 = None
        seq2= None
        identity = None
        similarity = None
        for line in wres:
            if line.startswith('# Program'):
                counter += 1
                logging.debug('Looking at next/new alignment.')
            elif line.startswith('# 1'):
                seq1 = line.strip().split(':')[1]
                logging.debug('Seq 1: {}'.format(seq1))
            elif line.startswith('# 2'):
                seq2 = line.strip().split(':')[1]
                logging.debug('Seq 2: {}'.format(seq2))
            elif line.startswith('# Identity'):
                id_tokens = line.strip().split()
                txt_id = id_tokens[-1][1:-2].strip()
                identity = str(round(float(txt_id) / 100, 2))
                logging.debug('Identity: {}'.format(identity))
            elif line.startswith('# Similarity'):
                sim_tokens = line.strip().split()
                txt_sim = sim_tokens[-1][1:-2].strip()
                similarity = str(round(float(txt_sim) / 100, 2))
                logging.debug('Similarity: {}'.format(similarity))
            elif line.startswith('#--'):
                if all([seq1, seq2, identity, similarity]):
                    alignment_partner = Partner(seq2, identity, similarity)
                    alignments[seq1].append(alignment_partner)
                    logging.debug(seq1, alignment_partner)
                    index.add(seq1)
                    seq1 = None
                    seq2= None
                    identity = None
                    similarity = None
        logging.info('Length of alignment index: {}'.format(str(len(index))))
        logging.info('Counted alignments: {}'.format(str(counter)))
        for k, v in alignments.items():
            alignments[k].sort(key=lambda partner: partner.seq)
        sorted_index = sorted(list(index))
        return (alignments, sorted_index)


def cleanup(path):
    files_to_remove = glob.glob(os.path.join(path, '*alignments.txt'))
    if files_to_remove:
        for file in files_to_remove:
            try:
                os.remove(file)
                logging.info('Cleaned up existing output file: {}'.format(file))
            except:
                logging.error('Cannot clean target dir of output file: {}'.format(file))


def svg_text_vertical(index_dict, seq):
    template = '<text x="{x}" y="{y}" font-size="10">{text}</text>'
    x = str(5)
    y = str(Y_INIT + index_dict[seq] * HEIGHT + HEIGHT)
    return template.format(x=x, y=y, text=seq)


def svg_text_horizontal(index_dict, seq):
    template = '<text x="{x}" y="{y}" font-size="10" transform = "rotate(-90 {x} {y})">{text}</text>'
    x = str(X_INIT + index_dict[seq] * WIDTH + WIDTH)
    y = Y_INIT - 3
    return template.format(x=x, y=y, text=seq)


def svg_guidelines(index_dict, seq):
    template = '<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:grey;stroke-width:2" />'
    x1 = str(X_INIT + index_dict[seq] * WIDTH + WIDTH / 2)
    y1 = Y_INIT
    x2 = x1
    y2 = Y_INIT + HEIGHT * index_dict[seq]
    return template.format(x1=x1, y1=y1, x2=x2, y2=y2)


def svg_rectangle(index_dict, seq, partner):
    x = str(X_INIT + (index_dict[seq] * WIDTH))
    y = str(Y_INIT + (index_dict[partner.seq] * HEIGHT))
    opa = partner.identity
    title = '{0}-{1}: {2}'.format(seq, partner.seq, partner.identity)
    logging.debug('Generated <rect> at {x}, {y} with opacity {opa} and title {title}'.format(x=x, y=y, opa=opa, title=title))
    return _svg_rect(x, y, opa, title)


def _svg_rect(x, y, opa, title):
    if opa == '1.0':
        color = 'green'
    else:
        color = 'blue'
    template = '<g><title>{title}</title><rect x="{x}" y="{y}" width="{w}" height="{h}" style="fill:{color};stroke:grey;stroke-width:1;fill-opacity:{opa}" /></g>'
    return template.format(x=x, y=y, w=WIDTH, h=HEIGHT, color=color, opa=opa, title=title)


def _filename_no_ext(path):
    fname = os.path.basename(path)
    name_no_ext = os.path.splitext(fname)
    return name_no_ext

def run():
    path = sys.argv[1]
    run_alignments(path)
    visualize_alignments(path)


if __name__ == "__main__":
    run()