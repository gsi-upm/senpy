#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#


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
