#!/usr/bin/env python

import os
import urllib
import json
import lxml.html

class Crawler(object):
    """docstring for Crawler"""
    BASE_URL='http://www.getlocalization.com'

    def __init__(self, project='mcmmo', language='en'):
        super(Crawler, self).__init__()
        self.project = project
        self.language = language
        self.locales =  self.get_locales()

    @property
    def string_list_url(self):
        """Get URL for stlist"""
        return "%s/%s/string_filter/?language=%s&filter=quality&duplicates=1" \
                % (self.BASE_URL, self.project, self.language)

    @property
    def string_data_url(self):
        """Get URL for string data"""
        return "%s/%s" % (self.BASE_URL, 'ajax/stringData/?string_id=')

    @property
    def string_translantion_url(self):
        """Get URL for striing translation"""
        return "%s/editor/pages/availableTranslations/?language_id=%s&string_id=" % (
            self.BASE_URL, self.locales[self.language])

    def fetch_url(self, url):
        """return html source data in unicode"""
        f = urllib.urlopen(url)
        data = f.read().decode('utf-8')
        f.close()
        return data
        
    def get_locales(self):
        """generate language tag/id mapping"""
        locales = {}
        langs = { 
            "Chinese (China)" : "zh-CN",
            "Chinese (Taiwan)" : "zh-TW",
            "Czech (Czech Republic)" : "cs-CZ",
            "Danish" : "da",
            "Dutch" : "nl",
            "English" : "en",
            "Finnish" : "fi",
            "French" : "fr",
            "German" : "de",
            "Hungarian (Hungary)" : "hu-HU",
            "Italian" : "it",
            "Japanese (Japan)" : "ja-JP",
            "Korean" : "ko",
            "Latvian" : "lv",
            "Lithuanian" : "lt",
            "Norwegian" : "no",
            "Polish": "pl",
            "Polish (Poland)": "pl-PL",
            "Portuguese (Brazil)" : "pt-BR",
            "Russian" : "ru",
            "Spanish" : "es",
            "Swedish" : "sv",
            "Thai (Thailand)" : "th-TH",
            "Turkish (Turkey)" : "tr-TR",
            "Welsh" : "cy",
        }
        data = self.fetch_url("%s/%s" % (self.BASE_URL, self.project))
        html = lxml.html.fromstring(data)
        for i in html.find_class('cell1'):
            a = i.find('a')
            if a != None:
                lang = a.text_content()
                code = a.get('href').replace('/',' ').split().pop()
                locales[langs[lang]] = code
        return locales

    def get_string_ids(self):
        """docstrig for get_string_ids"""
        ids = []
        data = self.fetch_url(self.string_list_url)
        html = lxml.html.fromstring(data)
        for i in html.findall('li'):
            ids.append(i.get('id').replace('pstring_', ''))
        return ids
    
    def get_string_context(self, id_):
        """docstring for get_string_context"""
        data = self.fetch_url("%s%s" % (self.string_data_url, id_))
        return json.loads(data)['context']
    
    def get_string_translation(self, id_):
        """docstring for get_string_translation"""
        data = self.fetch_url("%s%s" % (self.string_translantion_url, id_))
        html = lxml.html.fromstring(data) 
        winner = html.find_class('ot_row_winner')[0]
        string = winner.find_class('ot_string')[0].text_content()
        translation = winner.find_class('ot_translation')[0].text_content()
        return translation

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
    #print crawler.locales

