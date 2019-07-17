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

from senpy import PostProcessing, easy_test


class MaxEmotion(PostProcessing):
    '''Plugin to extract the emotion with highest value from an EmotionSet'''
    author = '@dsuarezsouto'
    version = '0.1'

    def process_entry(self, entry, activity):
        if len(entry.emotions) < 1:
            yield entry
            return

        set_emotions = entry.emotions[0]['onyx:hasEmotion']

        # If there is only one emotion, do not modify it
        if len(set_emotions) < 2:
            yield entry
            return

        max_emotion = set_emotions[0]

        # Extract max emotion from the set emotions (emotion with highest intensity)
        for tmp_emotion in set_emotions:
            if tmp_emotion['onyx:hasEmotionIntensity'] > max_emotion[
                    'onyx:hasEmotionIntensity']:
                max_emotion = tmp_emotion

        if max_emotion['onyx:hasEmotionIntensity'] == 0:
            max_emotion['onyx:hasEmotionCategory'] = "neutral"
            max_emotion['onyx:hasEmotionIntensity'] = 1.0

        entry.emotions[0]['onyx:hasEmotion'] = [max_emotion]

        entry.emotions[0]['prov:wasGeneratedBy'] = activity.id
        yield entry

    def check(self, request, plugins):
        return 'maxemotion' in request.parameters and self not in plugins

    # Test Cases:
    #   1 Normal Situation.
    #   2 Case to return a Neutral Emotion.
    test_cases = [
        {
            "name": "If there are several emotions within an emotion set, reduce it to one.",
            "entry": {
                "@type":
                "entry",
                "onyx:hasEmotionSet": [
                    {
                        "@id":
                        "Emotions0",
                        "@type":
                        "emotionSet",
                        "onyx:hasEmotion": [
                            {
                                "@id": "_:Emotion_1538121033.74",
                                "@type": "emotion",
                                "onyx:hasEmotionCategory": "anger",
                                "onyx:hasEmotionIntensity": 0
                            },
                            {
                                "@id": "_:Emotion_1538121033.74",
                                "@type": "emotion",
                                "onyx:hasEmotionCategory": "joy",
                                "onyx:hasEmotionIntensity": 0.3333333333333333
                            },
                            {
                                "@id": "_:Emotion_1538121033.74",
                                "@type": "emotion",
                                "onyx:hasEmotionCategory": "negative-fear",
                                "onyx:hasEmotionIntensity": 0
                            },
                            {
                                "@id": "_:Emotion_1538121033.74",
                                "@type": "emotion",
                                "onyx:hasEmotionCategory": "sadness",
                                "onyx:hasEmotionIntensity": 0
                            },
                            {
                                "@id": "_:Emotion_1538121033.74",
                                "@type": "emotion",
                                "onyx:hasEmotionCategory": "disgust",
                                "onyx:hasEmotionIntensity": 0
                            }
                        ]
                    }
                ],
                "nif:isString":
                "Test"
            },
            'expected': {
                "@type":
                "entry",
                "onyx:hasEmotionSet": [
                    {
                        "@id":
                        "Emotions0",
                        "@type":
                        "emotionSet",
                        "onyx:hasEmotion": [
                            {
                                "@id": "_:Emotion_1538121033.74",
                                "@type": "emotion",
                                "onyx:hasEmotionCategory": "joy",
                                "onyx:hasEmotionIntensity": 0.3333333333333333
                            }
                        ]
                    }
                ],
                "nif:isString":
                "Test"
            }
        },
        {
            "name":
            "If the maximum emotion has an intensity of 0, return a neutral emotion.",
            "entry": {
                "@type":
                "entry",
                "onyx:hasEmotionSet": [{
                    "@id":
                    "Emotions0",
                    "@type":
                    "emotionSet",
                    "onyx:hasEmotion": [
                        {
                            "@id": "_:Emotion_1538121033.74",
                            "@type": "emotion",
                            "onyx:hasEmotionCategory": "anger",
                            "onyx:hasEmotionIntensity": 0
                        },
                        {
                            "@id": "_:Emotion_1538121033.74",
                            "@type": "emotion",
                            "onyx:hasEmotionCategory": "joy",
                            "onyx:hasEmotionIntensity": 0
                        },
                        {
                            "@id":
                            "_:Emotion_1538121033.74",
                            "@type":
                            "emotion",
                            "onyx:hasEmotionCategory":
                            "negative-fear",
                            "onyx:hasEmotionIntensity":
                            0
                        },
                        {
                            "@id": "_:Emotion_1538121033.74",
                            "@type": "emotion",
                            "onyx:hasEmotionCategory":
                            "sadness",
                            "onyx:hasEmotionIntensity": 0
                        },
                        {
                            "@id": "_:Emotion_1538121033.74",
                            "@type": "emotion",
                            "onyx:hasEmotionCategory":
                            "disgust",
                            "onyx:hasEmotionIntensity": 0
                        }]
                }],
                "nif:isString":
                "Test"
            },
            'expected': {
                "@type":
                "entry",
                "onyx:hasEmotionSet": [{
                    "@id":
                    "Emotions0",
                    "@type":
                    "emotionSet",
                    "onyx:hasEmotion": [{
                        "@id": "_:Emotion_1538121033.74",
                        "@type": "emotion",
                        "onyx:hasEmotionCategory": "neutral",
                        "onyx:hasEmotionIntensity": 1
                    }]
                }],
                "nif:isString":
                "Test"
            }
        }
    ]


if __name__ == '__main__':
    easy_test()
