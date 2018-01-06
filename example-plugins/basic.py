#!/usr/local/bin/python
# coding: utf-8

emoticons = {
    'pos': [':)', ':]', '=)', ':D'],
    'neg': [':(', ':[', '=(']
}

emojis = {
    'pos': ['😁', '😂', '😃', '😄', '😆', '😅', '😄' '😍'],
    'neg': ['😢', '😡', '😠', '😞', '😖', '😔', '😓', '😒']
}


def get_polarity(text, dictionaries=[emoticons, emojis]):
    polarity = 'marl:Neutral'
    for dictionary in dictionaries:
        for label, values in dictionary.items():
            for emoticon in values:
                if emoticon and emoticon in text:
                    polarity = label
                    break
    return polarity
