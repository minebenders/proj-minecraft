from bs4 import BeautifulSoup
from pathlib import Path
import re
import json
import getopt
import sys
import logging

logging.basicConfig(level=logging.INFO)

STOPWORDS = ['and', 'the', 'for']
PROSEC_WHITELIST = ['rosecut', 'Attorney', 'AGC']
BLACKLIST = ['first|1st', 'second|2nd', 'third|3rd', 'fourth|4th', 'fifth|5th', 'sixth|6th', 'assistant', 'public', 'prosecutors?', 'prosecution', 'accused', 'defence', 'appellants?', 'respondents?', 'counsel', 'deputy', 'APP', 'AP', 'DPPs?', 'as', 'the', 'mr', 'ms', 'mrs', 'mdm', 'amicus', 'curiae', 'applicants?']
BLACKLIST_RE = re.compile(r'\b(?:%s)\b|\.|\,' % '|'.join(BLACKLIST), re.IGNORECASE)

def usage():
    print(f"usage: {sys.argv[0]} -i case_directory -o output.json")

def indexer(in_file):
    with open(in_file, 'r') as read_file:
        soup = BeautifulSoup(read_file, 'lxml')

    logging.info(f'Processing: "{in_file}"')
    case = {}
    
    def strip_inner_tag(children):
        return " ".join([child.string for child in children])

    def process_counsel(counsels):
        result = []
        for phrase in counsels:
            counsel = re.split(r'\(.*?\)|and |for |the | and| for| the|,|&| / ', phrase)
            counsel = [token for token in counsel if token.casefold() not in STOPWORDS]
            counsel = [re.sub(BLACKLIST_RE, '', token).strip() for token in counsel]
            counsel = [token.strip() for token in counsel if token.strip()]
            result.extend(counsel) 
        return set(result)

    # Case Reference
    case_ref = soup.select('span[class*="offhyperlink"]')
    if not case_ref:
        logging.warning('No Case Reference found.')
    else:
        case['reference'] = [ref.text.strip() for ref in case_ref]
        if len(case_ref) > 2:
            logging.warning(f'{len(case_ref)} Case Reference found: {case["reference"]}')
    
    # Other Info
    info_rows = soup.select('tr[class*="info-row"]')
    for tag in info_rows:
        label = tag.td.string
        content = tag.td.find_next_sibling('td', class_='txt-body')

        if len(content.contents) > 1:
            content_str = strip_inner_tag(content.children)
        else:
            content_str = content.string

        if label == 'Decision Date':
            case['date'] = content_str
        elif label == 'Tribunal/Court':
            case['court'] = content_str
        elif label == 'Coram':
            case['coram'] = [judge.string for judge in tag('a', class_='metadata-coram')]
        elif label == 'Counsel Name(s)':
            counsel_list = re.split(r';(?![^(]*\))', content_str)
            agc = [token for token in counsel_list if any(word in token for word in PROSEC_WHITELIST)]
            dfc = [token for token in counsel_list if token not in agc]
            case['counsel'] = dict()
            case['counsel'].update({'prosecution': list(process_counsel(agc))})
            case['counsel'].update({'defence': list(process_counsel(dfc))})
        elif label == 'Parties':
            case['parties'] = [re.sub('[()0-9]*', '', name).strip() for name in re.split('[-–—;]', content_str)]

    return case


input_directory = output_file = None

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

for i, f in enumerate(path.glob('*.htm*')):
    case = indexer(f)
    data.append(case)

with open(output_file, 'w') as w:
    json.dump(data, w, indent=2)

