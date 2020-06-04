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
URL = 'https://api.sal.sg/uat-legalresearch/v2/search'

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
    def search(searchTerm:str, cats:list, l2cats:list, l3cats:list,
               page:int=1, maxperpage:int=20, surroundingWords:int=10,
               orderBy:str='relevance'):
        args = locals()
        post = Post()
        for key, val in args.items():
            if type(val) is list:
                post._data.update({str(key): ','.join(val)})
            else:
                post._data.update({str(key): val})
        response = post._make_POST()
        xml_raw = post._process(response)
        return XMLResult(xml_raw)

    def _make_POST(self):
        return requests.post(URL, headers=self._headers, data=self._data, timeout=60)

    def _process(self, response):
        if response.status_code == 400:
            root = etree.XML(response.text)
            logging.warning(root[1].text)
            response.raise_for_status()
        if response.status_code == 403:
            self._refresh_token()
            new_response = self._make_POST()
            new_response.raise_for_status()
            return new_response
        return response

    def _refresh_token(self):
        Post._auth = auth().json()
        self._headers['Authorization'] = 'Bearer ' + self._auth['access_token']

class XMLResult:
    def __init__(self, xml_raw):
        self.raw = xml_raw.text
        self.data = self._xml_parse(xml_raw)

    def _xml_parse(self, xml_raw):
        results = []
        root = etree.XML(xml_raw.text)
        document_info = ['documentId', 'Title', 'Citation', 'relevance',
                         'category', 'court', 'corams', 'date', 'caseno',
                         'catchword',  'casereference']
        reference_info = ['following', 'referring', 'distinguishing',
                          'notfollowing', 'overruling']

        stat = root.find('searchStatistic')
        self.search_stats = {key: val for key, val in 
                                     zip([e.tag for e in stat],
                                         [e.text for e in stat])}

        xml_resultIter = root.iterfind('.//result')
        for xml_result in xml_resultIter:
            result = {}
            result['document_info'], result['reference_info'] = {}, {}
            for tag in document_info:
                result['document_info'][tag] = xml_result.find('.//' + tag).text
            for tag in reference_info:
                result['reference_info'][tag] = xml_result.find('.//' + tag).text
            results.append(self._clean_tags(result))

        return results

    def _clean_tags(self, result):
        result['document_info']['Title'] = ' '.join(
            result['document_info']['Title'].split())
        result['document_info']['catchword'] = list(
            set([cat.strip() for cat in result['document_info']['catchword'].split(',')]))

        return result
