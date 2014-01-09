#!/usr/bin/env python

# TODO: 1. Get username/password from input not from options.
#       2. Notice user if auth fail

"""Crawler
Usage:
  crawler.py fetch [-v] <username> <password> [--project=<name> --language=<code> --purge]
  crawler.py update [-v] <username> <password> (--id=<id>)
  crawler.py edit [-v] <translation> (--id=<id> | --context=<context>)
  crawler.py show [-v] (--id=<id> | --context=<context>)
  crawler.py list [-v]
  crawler.py make [-v] <path> [--format=<type>]
  crawler.py search [-v] <keyword>
  crawler.py (-h | --help)
  crawler.py (-V | --version)

Options:
  -h --help             Show this screen.
  -v --verbose          Verbose output [default: False].
  -V --version          Show version.
  --id=<id>             String ID.
  --context=<context>   String context.
  --project=<name>      Project name [default: mcmmo].
  --purge               Purge the cache file first.
  --format=<type>       Translation files format [default: java].
  --language=<code>     Language code [default: zh-TW].

"""

#import os
import urllib
import urllib2
import cookielib
import json
import pickle
import lxml.html
from docopt import docopt

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
        self.opener = None

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

    @property
    def login_url(self):
        """Login url for getlocalization.com"""
        return "%s/accounts/login/" % (self.BASE_URL)

    def fetch_url(self, url):
        """return html source data in unicode"""
        f = self.opener.open(url)
        data = f.read().decode('utf-8')
        f.close()
        return data

    def get_csrf_token(self, opener, cookiejar, login_url):
        """
        get csrf token from cookie
        ref: http://stackoverflow.com/questions/3623925/how-do-i-post-to-a-django-1-2-form-using-urllib
        """
        opener.open(login_url)
        token = [x.value for x in cookiejar if x.name == 'csrftoken'][0]
        return token

    def login(self, username, password):
        """login to getlocalization.com"""
        print "Login to getlocalization.com .."
        cookiejar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
        opener.addheaders.append(('Referer', self.login_url))
        token = self.get_csrf_token(opener, cookiejar, self.login_url)
        login_data = urllib.urlencode(
            {'username' : username,
             'password' : password,
             'csrfmiddlewaretoken' : token})
        opener.open(self.login_url, login_data)
        self.opener = opener

    def get_locales(self):
        """generate language tag/id mapping"""
        print "Check available languages .."
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
                if langs.has_key(lang):
                    locales[langs[lang]] = code
        return locales

    def get_string_ids(self):
        """docstrig for get_string_ids"""
        print "Check available items .."
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
        self.items[id_] = {
            'context' : context,
            'string' : string,
            'translation' : translation,
        }

    def fetch(self, username, password, resume=True):
        """fetch data"""
        #. init data
        self.login(username, password)
        self.locales = self.get_locales()
        ids = self.ids = self.get_string_ids()
        #. do my job
        i = 1
        for id_ in ids:
            if resume:
                #. don't fetch data if exist
                if id_ in self.items.keys():
                    i += 1
                    continue
            self.__fetch(id_)
            if self.verbose:
                print "[%s/%s] %s=%s" % (
                    i, len(ids),
                    self.items[id_]['context'], self.items[id_]['translation'])
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

    def update_item(self, username, password, id_):
        """update item in local cache from getlocalization.com"""
        self.login(username, password)
        self.locales = self.get_locales()
        self.__fetch(id_)
        self.pickle_dump()

if __name__ == '__main__':
    #. parse the args
    args = docopt(__doc__, version='Crawler 0.1')
    #print(arguments)

    #. init the crawler
    crawler = Crawler(
        project=args['--project'],
        language=args['--language'],
        verbose=args['--verbose'])

    #. do my job
    if args['fetch']:
        resume = False if args['--purge'] else True
        crawler.fetch(args['<username>'], args['<password>'], resume=resume)
    if args['list']:
        crawler.list_items()
    if args['make']:
        if args['--format'] == 'java':
            crawler.make_java_properties(args['<path>'])
        else:
            print("Current only support java only.")
    if args['search']:
        crawler.search_item(args['<keyword>'])
    if args['show']:
        if args['--id']:
            crawler.show_item_by_id(args['--id'])
        else:
            crawler.show_item_by_context(args['--context'])
    if args['edit']:
        if args['--id']:
            crawler.edit_item_by_id(args['--id'], args['<translation>'])
        else:
            crawler.edit_item_by_context(args['--id'], args['<translation>'])
    if args['update']:
        crawler.update_item(args['<username>'], args['<password>'], args['--id'])

