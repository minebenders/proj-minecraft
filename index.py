from indexer.info import Info
from indexer.body import Body
from pathlib import Path
from bs4 import BeautifulSoup
import json
import getopt
import sys
import logging


logging.basicConfig(level=logging.INFO)
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

for i, in_file in enumerate(sorted(path.glob('*.htm*'))):
    with open(in_file, 'r') as read_file:
        logging.info(f'Processing: "{in_file}"')
        soup = BeautifulSoup(read_file, 'lxml')
        case = Info.index(soup)
        case['paragraphs'] = Body.index(soup)
    data.append(case)

with open(output_file, 'w') as w:
    logging.info(f'Writing JSON to {output_file}')
    json.dump(data, w, indent=2)
