import json
import os
import requests
import base64
import logging
from lxml import etree
from getpass import getpass
from dotenv import load_dotenv
from auth import auth
from collections import defaultdict

load_dotenv()
URL = 'https://api.sal.sg/uat-legalresearch/v2/'

def get_api_keys():
    x_api_key = os.getenv('LN_X_API_KEY')
    if not x_api_key:
        x_api_key = getpass('Enter x-api_key: ')

    search_api_key = os.getenv('LN_SEARCH_API_KEY')
    if not search_api_key:
        search_api_key = getpass('Enter search-api_key: ')

    return x_api_key, search_api_key

class Post:
    _auth = auth().json()
    _x_api_key, _search_api_key = get_api_keys()

    def __init__(self):
        self._headers = {
            'Authorization': 'Bearer ' + self._auth['access_token'],
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-api_key': self._x_api_key
        }
        self._data = {
            'apikey': self._search_api_key
        }

    @staticmethod
    def search(searchTerm:str, cats:list=['r1'], l2cats:list=['r1c1'],
               l3cats:list=['#r1c1'], page:int=1, maxperpage:int=20, 
               surroundingWords:int=10, orderBy:str='relevance'):
        args = locals()
        post = Post()
        for key, val in args.items():
            if type(val) is list:
                post._data.update({str(key): ','.join(val)})
            else:
                post._data.update({str(key): val})
        response = post._make_POST('search')
        xml_raw = post._process(response)
        return _Parse.search_xml(xml_raw, page)

    @staticmethod
    def download(docUrl:str, cats:list=['r1'], l2cats:list=['r1c1'],
                 l3cats:list=['#r1c1'], filetype:str='xml'):
        assert (filetype in ['xml', 'pdf']), f'Unknown filetype: {filetype}'
        args = locals()
        post = Post()
        for key, val in args.items():
            if type(val) is list:
                post._data.update({str(key): ','.join(val)})
            elif str(key) == 'filetype':
                post._data.update({'format': val})
            else:
                post._data.update({str(key): val})
        response = post._make_POST('getContent')
        xml_raw = post._process(response)
        
        if filetype == 'xml':
            return _Parse.download_xml(xml_raw)
        elif filetype == 'pdf':
            return _Parse.download_pdf(xml_raw)

    def _make_POST(self, path):
        return requests.post(URL + path, headers=self._headers, data=self._data, timeout=60)

    def _process(self, response):
        if response.status_code == 400:
            root = etree.XML(response.text)
            logging.warning(root[1].text)
            response.raise_for_status()
        if response.status_code == 403:
            self._refresh_token()
            new_response = self._make_POST() #fix this
            new_response.raise_for_status()
            return new_response
        return response

    def _refresh_token(self):
        Post._auth = auth().json()
        self._headers['Authorization'] = 'Bearer ' + self._auth['access_token']

class XMLResult:
    def __init__(self, xml_string, parsed):
        try:
            self.raw = xml_string
            self.data = parsed
            for key, value in self.data.items():
                setattr(self, key.lower(), value)
        except AttributeError:
            logging.warning('Could not create XMLResult')

    def __repr__(self):
        return self.data['citation']

    def download(self, filetype='xml'):
        return Post.download(self.doc['documentId'], filetype=filetype)

class _Parse:
    @staticmethod
    def xml_node_recurse(node):
        answer = {}
        if len(node) == 0:
            return {node.tag.lower(): _Parse.str_to_boolean(node.text)}
        elif node.tag == 'snippets':
            snippets = []
            for snippet in node.iterchildren():
                snippets.append(etree.tostring(snippet, encoding='unicode',
                                               method='text'))
            answer.update({node.tag.lower(): snippets})
        else:
            for element in node.iterchildren():
                answer.update(_Parse.xml_node_recurse(element))
        return answer

    @staticmethod
    def str_to_boolean(text):
        if text.lower() in ('yes', 'no'):
            return text.lower() in ('yes')
        else:
            return text

    @staticmethod
    def search_xml(xml_raw, page):
        results = []
        root = etree.XML(xml_raw.text)

        stat = root.find('searchStatistic')
        search_stats = {key: val for key, val in 
                                     zip([e.tag for e in stat],
                                         [e.text for e in stat])}
        search_stats['page'] = page

        xml_resultIter = root.iterfind('.//result')
        for result_node in xml_resultIter:
            result_d = _Parse.xml_node_recurse(result_node)
            results.append(XMLResult(etree.tostring(result_node, encoding='UTF-8'),
                                     _Parse.clean_tags(result_d)))

        return results, search_stats
    
    @staticmethod
    def download_xml(xml_raw):
        root = etree.XML(xml_raw.text)
        case_report = root.find('CaseReport')
        
        return xml_raw

    @staticmethod
    def download_pdf(xml_raw):
        return xml_raw

    @staticmethod
    def clean_tags(result):
        result['title'] = ' '.join(
            result['title'].split())
        result['corams'] = result['corams'].replace(',', ';')
        result['corams'] = result['corams'].split(';')
        result['catchword'] = list(set(
            [cat.strip() for cat in result['catchword'].split(',')]))
        
        return result
