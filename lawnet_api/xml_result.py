import lawnet-api.search
import logging


class XMLResult:
    def __init__(self, xml_string, parsed):
        try:
            self.raw = xml_string
            self.doc = parsed['document_info']
            self.ref = parsed['reference_info']
            all_attr = {**self.doc, **self.ref}
            for key, value in all_attr.items():
                setattr(self, key.lower(), value)
        except AttributeError:
            logging.warning('Could not create XMLResult')

    def __repr__(self):
        return self.doc['Citation']

    def download(self, filetype='xml'):
        return Post.download(self.doc['documentId'], filetype=filetype)
