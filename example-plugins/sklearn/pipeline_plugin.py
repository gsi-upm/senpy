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

from senpy import SentimentBox, easy_test

from mypipeline import pipeline


class PipelineSentiment(SentimentBox):
    '''This is a pipeline plugin that wraps a classifier defined in another module
(mypipeline).'''
    author = '@balkian'
    version = 0.1
    maxPolarityValue = 1
    minPolarityValue = -1

    def predict_one(self, features, **kwargs):
        if pipeline.predict(features) > 0:
            return [1, 0, 0]
        return [0, 0, 1]

    test_cases = [
        {
            'input': 'The sentiment for senpy should be positive :)',
            'polarity': 'marl:Positive'
        },
        {
            'input': 'The sentiment for senpy should be negative :(',
            'polarity': 'marl:Negative'
        }
    ]


if __name__ == '__main__':
    easy_test()
