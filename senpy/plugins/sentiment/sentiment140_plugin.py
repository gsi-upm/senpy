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

ENDPOINT = 'http://www.sentiment140.com/api/bulkClassifyJson'


class Sentiment140(SentimentBox):
    '''Connects to the sentiment140 free API: http://sentiment140.com'''

    author = "@balkian"
    version = '0.2'
    url = "https://github.com/gsi-upm/senpy-plugins-community"
    extra_params = {
        'language': {
            "@id": 'lang_sentiment140',
            'description': 'language of the text',
            'aliases': ['language', 'l'],
            'required': True,
            'default': 'auto',
            'options': ['es', 'en', 'auto']
        }
    }

    classes = ['marl:Positive', 'marl:Neutral', 'marl:Negative']
    binary = True

    def predict_many(self, features, activity):
        lang = activity.params["language"]
        data = []

        for feature in features:
            data.append({'text': feature[0]})

        res = requests.post(ENDPOINT,
                            json.dumps({
                                "language": lang,
                                "data": data
                            }))

        for res in res.json()["data"]:
            polarity = int(res['polarity'])
            neutral_value = 2
            if polarity > neutral_value:
                yield [1, 0, 0]
                continue
            elif polarity < neutral_value:
                yield [0, 0, 1]
                continue
            yield [0, 1, 0]

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
            'responses': [{'url': ENDPOINT,
                           'method': 'POST',
                           'json': {'data': [{'polarity': 4}]}}]
        }
    ]
