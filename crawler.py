#!/usr/bin/env python

import os
import urllib
import json
from BeautifulSoup import BeautifulSoup


class Crawler(object):
    """docstring for Crawler"""
    URL_BASE='http://www.getlocalization.com'
    #. TODO: create language/id mapping
    LANGUAGES = {
        'en' : '5497',
        'zh-TW' : '10421',
    }
    def __init__(self, project='mcmmo', language='en'):
        super(Crawler, self).__init__()
        self.project = project
        self.language = language

    @property
    def string_list_url(self):
        """Get URL for stlist"""
        return "%s/%s/string_filter/?language=%s&filter=quality&duplicates=1" \
                % (self.URL_BASE, self.project, self.language)

    @property
    def string_data_url(self):
        """Get URL for string data"""
        return "%s/%s" % (self.URL_BASE, 'ajax/stringData/?string_id=')

    @property
    def string_translantion_url(self):
        """Get URL for striing translation"""
        return "%s/editor/pages/availableTranslations/?language_id=%s&string_id=" % (
            self.URL_BASE, self.LANGUAGES[self.language])
        
    def get_string_ids(self):
        """docstrig for get_string_ids"""
        ids = []
        f = urllib.urlopen(self.string_list_url)
        soap = BeautifulSoup(f.read())
        for li in soap.findAll("li"):
            ids.append(li.get('id').replace('pstring_', ''))
        return ids
    
    def get_string_context(self, id_):
        """docstring for get_string_context"""
        f = urllib.urlopen("%s%s" % (self.string_data_url, id_))
        return json.loads(f.read())['context']
    
    def get_string_translation(self, id_):
        """docstring for get_string_translation"""
        f = urllib.urlopen("%s%s" % (self.string_translantion_url, id_))
        soap = BeautifulSoup(f.read())
        return soap.findAll("td",{"class":"ot_translation"})[1].getString()

    def unicode_byte_string(self, string):
        """
        return unicode bye string, reference:
        http://code.activestate.com/recipes/466341-guaranteed-conversion-to-unicode-or-byte-string/
        """
        return unicode(string).encode('unicode_escape')
    
    def fetch(self, path):
        """fetch data"""
        ids = self.get_string_ids()
        try:
            os.unlink(path)
        except Exception:
            pass
        for id_ in ids:
            context = self.get_string_context(id_)
            translation = self.get_string_translation(id_)
            print "%s=%s" % (context, translation)
            with open(path, 'a') as f:
                f.write("%s=%s\n" % (
                    context, self.unicode_byte_string(translation)))

if __name__ == '__main__':
    crawler = Crawler(project='mcmmo', language='zh-TW')
    path='/tmp/zh_TW.locale'
    crawler.fetch(path)

