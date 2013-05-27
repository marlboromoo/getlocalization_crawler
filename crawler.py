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

    def safe_unicode(self, obj):
        """docstring for safe_unicode"""
        try:
            return obj.decode('utf8')
        except Exception:
            return unicode(obj)

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

    def __fetch(self, id_):
        """docstring for __fetch"""
        context = self.get_string_context(id_)
        string, translation = self.get_string_translation(id_)
        return context, string, translation
    
    def fetch(self, resume=True):
        """fetch data"""
        ids = self.ids = self.get_string_ids()
        i = 1
        print ids
        for id_ in ids:
            if resume:
                #. don't fetch data if exist
                if id_ in self.items.keys():
                    i += 1
                    continue
            #context = self.get_string_context(id_)
            #string, translation = self.get_string_translation(id_)
            context, string, translation = self.__fetch(id_)
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
        except Exception:
            print "Make fail."

    def __show_item(self, id_, attrs, short=True):
        """swho pretty item"""
        print "%s" % ('='*80)
        print "Id: %s Context: %s" % (id_, attrs['context'])
        string = "%s ..." % attrs['string'][:26] if short else attrs['string']
        tran = "%s ..." % attrs['translation'][:26] if short else attrs['translation']
        print "String: %s\nTranslation: %s" % (string, tran)

    def __show_summary(self):
        """docstring for __show_summary"""
        pass

    def show_item_by_id(self, id_):
        """show item by id"""
        if id_ in self.items:
            self.__show_item(id_, self.items[id_], short=False)

    def get_id_by_context(self, context):
        """get id by context"""
        for k,v in self.items.items():
            if context == v['context']:
                return k

    def show_item_by_context(self, context):
        """docstring for show_item_by_context"""
        id_ = self.get_id_by_context(context)
        if id_:
            return self.show_item_by_id(id_)

    def list_items(self):
        """list all items"""
        for k,v in self.items.items():
            self.__show_item(k, v)

    def search_item(self, keyword):
        """search item by keyword"""
        keyword = keyword.lower()
        result = {}
        for k,v in self.items.items():
            if keyword in v['string']:
                result[k] = v
        for k,v in result.items():
            self.__show_item(k,v)

    def edit_item_by_id(self, id_, translation):
        """edit translation for specific id"""
        if id_ in self.items:
            self.items[id_]['translation'] = self.safe_unicode(translation)
        self.pickle_dump()

    def edit_item_by_context(self, context, translation):
        """edit translation for specific context"""
        id_ = self.get_id_by_context(context)
        if id_:
            return self.edit_item_by_id(id_)

    def update(self, id_):
        """docstring for update"""
        pass

def main():
    """docstring for """
parser = argparse.ArgumentParser()                                          
subparsers = parser.add_subparsers(
    dest='cmd', title='command')
#. cmd: fetch
parser_fetch = subparsers.add_parser(
    'fetch', help="fetch data from getlocalization.com")
#. cmd: list
parser_list = subparsers.add_parser(
    'list', help="list data from local cache")
#. cmd: make
parser_make = subparsers.add_parser(
    'make', help="generate file with specific type from local cache")
parser_make.add_argument(
    'path', help="path to writing file")
parser_make.add_argument(
    '--type', default='java', choices=['java', '..'])
#. cmd: search
parser_search = subparsers.add_parser(
    'search', help="search item from local cache")
parser_search.add_argument(
    'keyword', help="keyword to search")
#. cmd: show
parser_show = subparsers.add_parser(
    'show', help="show the item from local cache")
#. cmd: edit
parser_edit = subparsers.add_parser(
    'edit', help="edit the translation in the local cache")
parser_edit.add_argument(
    'translation', help="new translation to update")
#. global args
group_target= parser.add_mutually_exclusive_group()
group_target.add_argument(
    '--id', help="specify the id")
group_target.add_argument(
    '--context', help="specify the context")
parser.add_argument(
    '--project', default='mcmmo', help="project to crawl, default: mcmmo")
parser.add_argument(
    '--lang', default='zh-TW', help="language to crawl, default: zh-TW")
parser.add_argument(
    '--no_resume', action='store_true', help="no resuming download")
parser.add_argument(
    '--no_verbose', action='store_true', help="no verbose output")
#. parse args
args = parser.parse_args()     
verbose = False if args.no_verbose else True
resume = False if args.no_resume else True
#. do my job
crawler = Crawler(project=args.project, language=args.lang)
if args.cmd == 'fetch':
    crawler.fetch(resume=resume)
if args.cmd == 'list':
    crawler.list_items()
if args.cmd == 'make':
    if args.type == 'java':
        crawler.make_java_properties(args.path)
if args.cmd == 'search':
    crawler.search_item(args.keyword)
target_err_msg = "Use with option --id or --context"
if args.cmd == 'show':
    if args.id:
        crawler.show_item_by_id(args.id)
    elif args.context:
        crawler.show_item_by_context(args.context)
    else:
        print "%s" % (target_err_msg)
if args.cmd == 'edit':
    if args.id:
        crawler.edit_item_by_id(args.id, args.translation)
    elif args.context:
        crawler.edit_item_by_context(args.id, args.translation)
    else:
        print "%s" % (target_err_msg)

if __name__ == '__main__':
    main()


