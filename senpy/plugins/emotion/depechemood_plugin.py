#!/usr/local/bin/python
# coding: utf-8

from future import standard_library
standard_library.install_aliases()

import os
import re
import sys
import string
import numpy as np
from six.moves import urllib
from nltk.corpus import stopwords

from senpy import EmotionBox, models


def ignore(dchars):
    deletechars = "".join(dchars)
    tbl = str.maketrans("", "", deletechars)
    ignore = lambda s: s.translate(tbl)
    return ignore


class DepecheMood(EmotionBox):
    '''
    Plugin that uses the DepecheMood emotion lexicon.

    DepecheMood is an emotion lexicon automatically generated from news articles where users expressed their associated emotions. It contains two languages (English and Italian), as well as three types of word representations (token, lemma and lemma#PoS). For English, the lexicon contains 165k tokens, while the Italian version contains 116k. Unsupervised techniques can be applied to generate simple but effective baselines. To learn more, please visit https://github.com/marcoguerini/DepecheMood and http://www.depechemood.eu/
    '''

    author = 'Oscar Araque'
    name = 'emotion-depechemood'
    version = '0.1'
    requirements = ['pandas']
    optional = True
    nltk_resources = ["stopwords"]

    onyx__usesEmotionModel = 'wna:WNAModel'

    EMOTIONS =  ['wna:negative-fear',
                 'wna:amusement',
                 'wna:anger',
                 'wna:annoyance',
                 'wna:indifference',
                 'wna:joy',
                 'wna:awe',
                 'wna:sadness']

    DM_EMOTIONS = ['AFRAID', 'AMUSED', 'ANGRY', 'ANNOYED', 'DONT_CARE', 'HAPPY', 'INSPIRED', 'SAD',]

    def __init__(self, *args, **kwargs):
        super(DepecheMood, self).__init__(*args, **kwargs)
        self.LEXICON_URL = "https://github.com/marcoguerini/DepecheMood/raw/master/DepecheMood%2B%2B/DepecheMood_english_token_full.tsv"
        self._denoise = ignore(set(string.punctuation)|set('«»'))
        self._stop_words = []
        self._lex_vocab = None
        self._lex = None

    def activate(self):
        self._lex = self.download_lex()
        self._lex_vocab = set(list(self._lex.keys()))
        self._stop_words = stopwords.words('english') + ['']

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
        tokens = self._denoise(self.clean_str(text)).split(' ')
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
        S = []
        intersection = set(tokens) & self._lex_vocab
        for emotion in self.DM_EMOTIONS:
            s = self.estimate_emotion(intersection, emotion)
            S.append(s)
        return S

    def download_lex(self, file_path='DepecheMood_english_token_full.tsv', freq_threshold=10):

        import pandas as pd

        try:
            file_path = self.find_file(file_path)
        except IOError:
            file_path = self.path(file_path)
            filename, _ = urllib.request.urlretrieve(self.LEXICON_URL, file_path)

        lexicon = pd.read_csv(file_path, sep='\t', index_col=0)
        lexicon = lexicon[lexicon['freq'] >= freq_threshold]
        lexicon.drop('freq', axis=1, inplace=True)
        lexicon = lexicon.T.to_dict()
        return lexicon

    def predict_one(self, features, **kwargs):
        tokens = self.preprocess(features[0])
        estimation = self.estimate_all_emotions(tokens)
        return estimation

    test_cases = [
        {
            'entry': {
                'nif:isString': 'My cat is very happy',
            },
            'expected': {
                'onyx:hasEmotionSet': [
                    {
                        'onyx:hasEmotion': [
                            {
                             'onyx:hasEmotionCategory': 'wna:negative-fear',
                             'onyx:hasEmotionIntensity': 0.05278117640010922
                            },
                            {
                                'onyx:hasEmotionCategory': 'wna:amusement',
                                'onyx:hasEmotionIntensity': 0.2114806151413433,
                            },
                            {
                                'onyx:hasEmotionCategory': 'wna:anger',
                                'onyx:hasEmotionIntensity': 0.05726119426520887
                            },
                            {
                                'onyx:hasEmotionCategory': 'wna:annoyance',
                                'onyx:hasEmotionIntensity': 0.12295990731053638,
                            },
                            {
                                'onyx:hasEmotionCategory': 'wna:indifference',
                                'onyx:hasEmotionIntensity': 0.1860159893608025,
                            },
                            {
                                'onyx:hasEmotionCategory': 'wna:joy',
                                'onyx:hasEmotionIntensity': 0.12904050973724163,
                            },
                            {
                                'onyx:hasEmotionCategory': 'wna:awe',
                                'onyx:hasEmotionIntensity': 0.17973650399862967,
                            },
                            {
                                'onyx:hasEmotionCategory': 'wna:sadness',
                                'onyx:hasEmotionIntensity': 0.060724103786128455,
                            },
                        ]
                    }
                ]
            }
        }
    ]


if __name__ == '__main__':
    from senpy.utils import easy_test
    easy_test(debug=False)
