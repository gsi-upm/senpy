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

import requests
import json

from senpy.plugins import SentimentBox
from senpy import easy_test

ENDPOINT = 'http://sentiment.gelbukh.com/sentiment/run.php'


class Senticnet(SentimentBox):
    '''Connects to the SenticNet free polarity detection API: http://sentiment.gelbukh.com/sentiment/'''

    author = "@balkian"
    version = '0.1'
    url = "https://github.com/gsi-upm/senpy-plugins-community"
    extra_params = {
    }

    classes = ['marl:Positive', 'marl:Neutral', 'marl:Negative']
    binary = True

    def predict_one(self, features, activity):
        text = ' '.join(features)

        res = requests.post(ENDPOINT,
                            data={'input':  text})

        if '-' not in res.text:
            raise Exception('Invalid response from server: {}'.format(res.text))

        label = res.text.split('-')[1].lower()

        if 'positive' in label:
            return [1, 0, 0]
        elif 'negative' in label:
            return [0, 0, 1]

        return [0, 1, 0]

    test_cases = [
        {
            'entry': {
                'nif:isString': 'I love Titanic'
            },
            'params': {},
            'expected': {
                "nif:isString": "I love Titanic",
                'marl:hasOpinion': [
                    {
                        'marl:hasPolarity': 'marl:Positive',
                    }
                ]
            },
        }, {
            'entry': {
                'nif:isString': 'I hate my life'
            },
            'params': {},
            'expected': {
                "nif:isString": "I hate my life",
                'marl:hasOpinion': [
                    {
                        'marl:hasPolarity': 'marl:Negative',
                    }
                ]
            },
        }, 
    ]

if __name__ == '__main__':
    easy_test()
