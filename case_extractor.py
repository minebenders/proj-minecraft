import getopt
import json
import logging
import argparse

from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
from indexer.body import Body
from indexer.info import Info
from indexer.pbar import TqdmLoggingHandler

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(TqdmLoggingHandler())

input_directory = output_file = None

parser = argparse.ArgumentParser(
    description='''Extracts data from the .html files from a source directory.
                   Argument defaults for the input directory and output file are ./cases/ and output.json.''')
parser.add_argument('-i', help="location of the directory containing the cases (default: cases)",
                    default="cases", dest="input_directory")
parser.add_argument('-o', help="output filename (default: output.json)",
                    default="output.json", dest="output_file")

arguments = parser.parse_args()
input_directory = Path(arguments.input_directory)
output_file = arguments.output_file

if input_directory.exists():
    data = []
    previous_case = {}

    for i, in_file in enumerate(tqdm(sorted(input_directory.glob('*.htm*')))):
        with open(in_file, 'r', encoding='utf-8', errors='ignore') as read_file:
            log.debug(f'Processing: "{in_file}"')
            soup = BeautifulSoup(read_file, 'lxml')
            case = Info.index(soup, in_file)
            if Body.index(soup):
                case['paragraphs'] = Body.index(soup)
        if case and case != previous_case:
            data.append(case)
            previous_case = case

    with open(output_file, 'w') as w:
        log.info(f'Writing JSON to {output_file}')
        json.dump(data, w, indent=2)
    log.info(f'JSON saved as {output_file}')

else:
    log.error(
        f'Directory "{input_directory}" was not found. Run `python index.py -h` for help.')
