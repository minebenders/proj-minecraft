from bs4 import BeautifulSoup
import unicodedata
import re
import logging


class Body:
    def index(soup):
        paragraphs = []
        temp = ""
        para_soup = soup("p", {"class": re.compile("Judg-\d+")})

        for p in para_soup:
            if "Judg-1" not in p['class']:
                para = Body.merge(p.strings)
                temp += "\n" + para
            else:
                if temp:
                    paragraphs[-1] += temp
                    temp = ''
                para = Body.merge(p.strings)
                paragraphs.append(re.sub(r'^\d{1,3}', '', para))

        result = {i: para.lstrip()
                  for i, para in enumerate(paragraphs, start=1)}
        return result

    def merge(strings):
        para = unicodedata.normalize(
                'NFKC', ''.join([string for string in strings]))
        return para
