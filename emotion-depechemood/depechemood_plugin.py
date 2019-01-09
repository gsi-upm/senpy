#!/usr/local/bin/python
# coding: utf-8

import os
import re
import string
import numpy as np
import pandas as pd
from six.moves import urllib
from nltk.corpus import stopwords

from senpy import EmotionPlugin, TextBox, models


class DepecheMood(TextBox, EmotionPlugin):
    '''Plugin that uses the DepecheMood++ emotion lexicon.'''

    author = 'Oscar Araque'
    version = '0.1'

    def __init__(self, *args, **kwargs):
        super(DepecheMood, self).__init__(*args, **kwargs)
        self.LEXICON_URL = "https://github.com/marcoguerini/DepecheMood/raw/master/DepecheMood%2B%2B/DepecheMood_english_token_full.tsv"
        self.EMOTIONS = ['AFRAID', 'AMUSED', 'ANGRY', 'ANNOYED', 'DONT_CARE', 'HAPPY', 'INSPIRED', 'SAD',]
        self._mapping = {
            'AFRAID': 'wna:negative-fear',
            'AMUSED': 'wna:amusement',
            'ANGRY': 'wna:anger',
            'ANNOYED': 'wna:annoyance',
            'DONT_CARE': 'wna:indifference',
            'HAPPY': 'wna:joy',
            'INSPIRED': 'wna:awe',
            'SAD': 'wna:sadness',
        }
        self._noise = self.__noise() 
        self._stop_words = stopwords.words('english') + ['']
        self._lex_vocab = None
        self._lex = None

    def __noise(self):
        noise = set(string.punctuation) | set('«»')
        noise = {ord(c): None for c in noise}
        return noise

    def activate(self):
        self._lex = self.download_lex()
        self._lex_vocab = set(list(self._lex.keys()))

    def clean_str(self, string):
        string = re.sub(r"[^A-Za-z0-9().,!?\'\`]", " ", string)
        string = re.sub(r"[0-9]+", " num ", string)
        string = re.sub(r"\'s", " \'s", string)
        string = re.sub(r"\'ve", " \'ve", string)
        string = re.sub(r"n\'t", " n\'t", string)
        string = re.sub(r"\'re", " \'re", string)
        string = re.sub(r"\'d", " \'d", string)
        string = re.sub(r"\'ll", " \'ll", string)
        string = re.sub(r"\.", " . ", string)
        string = re.sub(r",", " , ", string)
        string = re.sub(r"!", " ! ", string)
        string = re.sub(r"\(", " ( ", string)
        string = re.sub(r"\)", " ) ", string)
        string = re.sub(r"\?", " ? ", string)
        string = re.sub(r"\s{2,}", " ", string)
        return string.strip().lower()

    def preprocess(self, text):
        if text is None:
            return None
        tokens = self.clean_str(text).translate(self._noise).split(' ')
        tokens = [tok for tok in tokens if tok not in self._stop_words]
        return tokens   

    def estimate_emotion(self, tokens, emotion):
        s = []
        for tok in tokens:
            s.append(self._lex[tok][emotion])
        dividend = np.sum(s) if np.sum(s) > 0 else 0
        divisor = len(s) if len(s) > 0 else 1
        S = np.sum(s) / divisor
        return S

    def estimate_all_emotions(self, tokens):
        S = {}
        intersection = set(tokens) & self._lex_vocab
        for emotion in self.EMOTIONS:
            s = self.estimate_emotion(intersection, emotion)
            emotion_mapped = self._mapping[emotion]
            S[emotion_mapped] = s
        return S

    def download_lex(self, file_path='DepecheMood_english_token_full.tsv', freq_threshold=10):

        try:
            file_path = self.find_file(file_path)
        except IOError:
            filename, _ = urllib.request.urlretrieve(self.LEXICON_URL, file_path)

        lexicon = pd.read_csv(file_path, sep='\t', index_col=0)
        lexicon = lexicon[lexicon['freq'] >= freq_threshold]
        lexicon.drop('freq', axis=1, inplace=True)
        lexicon = lexicon.T.to_dict()
        return lexicon

    def output(self, output, entry, **kwargs):
        s = models.EmotionSet()
        s.prov__wasGeneratedBy = self.id
        entry.emotions.append(s)
        for label, value in output.items():
            e = models.Emotion(onyx__hasEmotionCategory=label,
                               onyx__hasEmotionIntensity=value)
            s.onyx__hasEmotion.append(e)
        return entry

    def predict_one(self, input, **kwargs):
        tokens = self.preprocess(input)
        estimation = self.estimate_all_emotions(tokens)
        return estimation

    test_cases = [
        {
            'entry': {
                'nif:isString': 'My cat is very happy',
            },
            'expected': {
                'emotions': [
                    {
                        '@type': 'emotionSet',
                        'onyx:hasEmotion': [
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:negative-fear',
                             'onyx:hasEmotionIntensity': 0.05278117640010922, },
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:amusement',
                             'onyx:hasEmotionIntensity': 0.2114806151413433, },
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:anger',
                             'onyx:hasEmotionIntensity': 0.05726119426520887, },
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:annoyance',
                             'onyx:hasEmotionIntensity': 0.12295990731053638, },
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:indifference',
                             'onyx:hasEmotionIntensity': 0.1860159893608025, },
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:joy',
                             'onyx:hasEmotionIntensity': 0.12904050973724163, },
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:awe',
                             'onyx:hasEmotionIntensity': 0.17973650399862967, },
                            {'@type': 'emotion', 'onyx:hasEmotionCategory': 'wna:sadness',
                                'onyx:hasEmotionIntensity': 0.060724103786128455, },
                        ]
                    }
                ]
            }
        }
    ]


if __name__ == '__main__':
    from senpy.utils import easy, easy_load, easy_test
    # sp, app = easy_load()
    # for plug in sp.analysis_plugins:
    #     plug.test()
    easy()
