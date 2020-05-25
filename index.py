import getopt
import json
import logging
import sys

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


def usage():
    print(f"usage: {sys.argv[0]} -i case_directory -o output.json")


try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for opt, arg in opts:
    if opt == '-i':
        input_directory = arg
    elif opt == '-o':
        output_file = arg
    else:
        assert False, "unknown option"

if input_directory is None or output_file is None:
    usage()
    sys.exit(2)

path = Path(input_directory)
data = []
previous_case = {}

for i, in_file in enumerate(tqdm(sorted(path.glob('*.htm*')))):
    with open(in_file, 'r', encoding='utf-8', errors='ignore') as read_file:
        log.debug(f'Processing: "{in_file}"')
        soup = BeautifulSoup(read_file, 'lxml')
        case = Info.index(soup, in_file)
        if Body.index(soup):
            case['paragraphs'] = Body.index(soup)
    if case and case != previous_case:
        data.append(case)
        previous_case = case

try:
    with open(output_file, 'w') as w:
        log.info(f'Writing JSON to {output_file}')
        json.dump(data, w, indent=2)
    log.info(f'JSON saved as {output_file}')
except:
    log.warning(f'Failed to save to {output_file}')
