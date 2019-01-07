#!/usr/local/bin/python
# -*- coding: utf-8 -*-

emoticons = {
    'pos': [':)', ':]', '=)', ':D'],
    'neg': [':(', ':[', '=(']
}

emojis = {
    'pos': [u'😁', u'😂', u'😃', u'😄', u'😆', u'😅', u'😄', u'😍'],
    'neg': [u'😢', u'😡', u'😠', u'😞', u'😖', u'😔', u'😓', u'😒']
}


def get_polarity(text, dictionaries=[emoticons, emojis]):
    polarity = 'marl:Neutral'
    print('Input for get_polarity', text)
    for dictionary in dictionaries:
        for label, values in dictionary.items():
            for emoticon in values:
                if emoticon and emoticon in text:
                    polarity = label
                    break
    print('Polarity', polarity)
    return polarity
