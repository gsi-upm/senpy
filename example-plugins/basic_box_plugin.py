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

from senpy import easy_test, SentimentBox

import basic


class BasicBox(SentimentBox):
    ''' A modified version of Basic that also does converts annotations manually'''

    author = '@balkian'
    version = '0.1'

    def predict_one(self, features, **kwargs):
        output = basic.get_polarity(features[0])
        if output == 'pos':
            return [1, 0, 0]
        if output == 'neg':
            return [0, 0, 1]
        return [0, 1, 0]

    test_cases = [{
        'input': 'Hello :)',
        'polarity': 'marl:Positive'
    }, {
        'input': 'So sad :(',
        'polarity': 'marl:Negative'
    }, {
        'input': 'Yay! Emojis  😁',
        'polarity': 'marl:Positive'
    }, {
        'input': 'But no emoticons 😢',
        'polarity': 'marl:Negative'
    }]


if __name__ == '__main__':
    easy_test()
