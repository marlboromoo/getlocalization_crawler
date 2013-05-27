#!/usr/bin/env python

#import os
import urllib
import json
import pickle
import argparse
import lxml.html

class Crawler(object):
    """docstring for Crawler"""
    BASE_URL='http://www.getlocalization.com'

    def __init__(self, 
                 project='mcmmo', language='en', path='/tmp/locale',
                 verbose=True,
                ):
        super(Crawler, self).__init__()
        self.project = project
        self.language = language
        self.path = path
        self.verbose=verbose
        self.pickle_path = "%s_%s_%s.p" % (path, project, language)
        self.pickle_load()
        self.locales = {}
        self.ids = []

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
        self.locales =  self.get_locales()
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
        print "Generate language ids .."
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
        return (unicode(string), unicode(translation))

    def unicode_byte_string(self, string):
        """
        return unicode bye string, reference:
        http://code.activestate.com/recipes/466341-guaranteed-conversion-to-unicode-or-byte-string/
        """
        return unicode(string).encode('unicode_escape')

    def pickle_dump(self):
        """docstring for pickle_dump"""
        pickle.dump(self.items, open(self.pickle_path, 'wb'))

    def pickle_load(self):
        """docstring for pickle_load"""
        try:
            self.items = pickle.load(open(self.pickle_path, 'rb'))
        except Exception:
            self.items = {}
            print 'No existing pickle file!'
    
    def fetch(self, resume=True):
        """fetch data"""
        ids = self.ids = self.get_string_ids()
        i = 1
        for id_ in ids:
            if resume:
                #. don't fetch data if exist
                if id_ in self.items.keys():
                    i += 1
                    continue
            context = self.get_string_context(id_)
            string, translation = self.get_string_translation(id_)
            if self.verbose:
                print "[%s/%s] %s=%s" % (i, len(ids), context, translation)
            self.items[id_] = {
                'context' : context,
                'string' : string,
                'translation' : translation,
            }
            i += 1
            #. dump to disk every 10 items
            if i % 10 == 0:
                self.pickle_dump()
        self.pickle_dump()

    def make_java_properties(self, path):
        """docstring for make_java_properties"""
        try:
            with open(path, 'w') as f:
                for k,v in self.items.items():
                    f.write("%s=%s\n" % (
                        v['context'], self.unicode_byte_string(v['translation'])))
        except Exception, e:
            raise e

    def list_items(self):
        """docstring for """
        print self.items
        for k,v in self.items.items():
            print "id:%s context:%s" % (k, v['context'])
            print "string:%s\ntranslation:%s" % (v['string'], v['translation'])

def main():
    """docstring for """
parser = argparse.ArgumentParser()                                          
#. commands
subparsers = parser.add_subparsers(dest='cmd', title='command', help='valid commands')
parser_fetch = subparsers.add_parser('fetch', help="fetch data from getlocalization.com.")
parser_list = subparsers.add_parser('list', help="list data from local cache.")
parser_make = subparsers.add_parser('make', help="generate file with specify project type.")
parser_make.add_argument('--type', default='java', choices=['java', '..'])
#. global args
parser.add_argument('--project', default='mcmmo', help="project to crawl, default: mcmmo.")
parser.add_argument('--lang', default='zh-TW', help="language to crawl, default: zh-TW")
parser.add_argument('--no_reume', action='store_true', help="no resuming download.")
parser.add_argument('--no_verbose', action='store_true', help="no verbose output.")
#. parse args
args = parser.parse_args()     
verbose = False if args.no_verbose else True
resume = False if args.no_reume else True
#. do my job
crawler = Crawler(project=args.project, language=args.lang)
if args.cmd == 'fetch':
    crawler.fetch(resume=resume)
if args.cmd == 'list':
    crawler.list_items()
if args.cmd == 'make':
    path='/tmp/zh_TW.locale'
    crawler.make_java_properties(path)

if __name__ == '__main__':
    main()


