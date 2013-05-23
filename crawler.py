#!/usr/bin/env python

import os
import urllib
import json
from BeautifulSoup import BeautifulSoup

URL_STRING_LIST='http://www.getlocalization.com/mcmmo/string_filter/?language=zh-TW&filter=quality&duplicates=1'
URL_STRING_DATA='http://www.getlocalization.com/ajax/stringData/?string_id='
URL_STRING_TRANSLATION='http://www.getlocalization.com/editor/pages/availableTranslations/?language_id=10421&string_id='

def get_string_ids():
    """docstring for get_string_ids"""
    ids = []
    f = urllib.urlopen(URL_STRING_LIST)
    soap = BeautifulSoup(f.read())
    for li in soap.findAll("li"):
        ids.append(li.get('id').replace('pstring_', ''))
    return ids

def get_string_context(id_):
    """docstring for get_string_context"""
    f = urllib.urlopen("%s%s" % (URL_STRING_DATA, id_))
    return json.loads(f.read())['context']

def get_string_translation(id_):
    """docstring for get_string_translation"""
    f = urllib.urlopen("%s%s" % (URL_STRING_TRANSLATION, id_))
    soap = BeautifulSoup(f.read())
    return soap.findAll("td",{"class":"ot_translation"})[1].getString()

if __name__ == '__main__':
    ids = get_string_ids()
    path='/tmp/zh_TW.locale'
    try:
        os.unlink(path)
    except Exception:
        pass
    for id_ in ids:
        context = get_string_context(id_)
        translation = get_string_translation(id_)
        print "%s=%s" % (context, translation)
        #. ref: http://code.activestate.com/recipes/466341-guaranteed-conversion-to-unicode-or-byte-string/
        with open(path, 'a') as f:
            f.write("%s=%s\n" % (context, unicode(translation).encode('unicode_escape')))

