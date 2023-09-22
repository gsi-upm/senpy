#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import string
import nltk
import pickle

from sentiwn import SentiWordNet
from nltk.corpus import wordnet as wn
from textblob import TextBlob
from scipy.interpolate import interp1d
from os import path

from senpy.plugins import SentimentBox, SenpyPlugin
from senpy.models import Results, Entry, Sentiment, Error

if sys.version_info[0] >= 3:
    unicode = str


class SentimentBasic(SentimentBox):
    '''
    Sentiment classifier using rule-based classification for Spanish. Based on english to spanish translation and SentiWordNet sentiment knowledge. This is a demo plugin that uses only some features from the TASS 2015 classifier. To use the entirely functional classifier you can use the service in: http://senpy.cluster.gsi.dit.upm.es.
    '''
    name = "sentiment-basic"
    author = "github.com/nachtkatze"
    version = "0.1.1"
    extra_params = {
        "language": {
            "description": "language of the text",
            "aliases": ["language", "l"],
            "required": True,
            "options": ["en","es", "it", "fr"],
            "default": "en"
        }
    }
    sentiword_path = "SentiWordNet_3.0.txt"
    pos_path = "unigram_spanish.pickle"
    maxPolarityValue = 1
    minPolarityValue = -1
    nltk_resources = ['punkt','wordnet', 'omw', 'omw-1.4']

    with_polarity = False

    def _load_swn(self):
        self.swn_path = self.find_file(self.sentiword_path)
        swn = SentiWordNet(self.swn_path)
        return swn

    def _load_pos_tagger(self):
        self.pos_path = self.find_file(self.pos_path)
        with open(self.pos_path, 'rb') as f:
            tagger = pickle.load(f)
        return tagger

    def activate(self, *args, **kwargs):
        self._swn = self._load_swn()
        self._pos_tagger = self._load_pos_tagger()

    def _remove_punctuation(self, tokens):
        return [t for t in tokens if t not in string.punctuation]

    def _tokenize(self, text):
        sentence_ = {}
        words = nltk.word_tokenize(text)
        sentence_['sentence'] = text
        tokens_ = [w.lower() for w in words]
        sentence_['tokens'] = self._remove_punctuation(tokens_)
        return sentence_

    def _pos(self, tokens):
        tokens['tokens'] = self._pos_tagger.tag(tokens['tokens'])
        return tokens

    def _compare_synsets(self, synsets, tokens):
        for synset in synsets:
            for word, lemmas in tokens['lemmas'].items():
                for lemma in lemmas:
                    synset_ = lemma.synset() 
                    if synset == synset_:
                        return synset
        return None

    def predict_one(self, features, activity):
        language = activity.param("language")
        text = features[0]
        tokens = self._tokenize(text)
        tokens = self._pos(tokens)
        sufixes = {'es':'spa','en':'eng','it':'ita','fr':'fra'}
        tokens['lemmas'] = {}
        for w in tokens['tokens']:
            lemmas = wn.lemmas(w[0], lang=sufixes[language])
            if len(lemmas) == 0:
                continue
            tokens['lemmas'][w[0]] = lemmas
        if language == "en":
            trans = TextBlob(unicode(text))
        else:
            try:
                trans = TextBlob(unicode(text)).translate(from_lang=language,to='en')
            except Exception as ex:
                raise Error('Could not translate the text from "{}" to "{}": {}'.format(language,
                                                                                    'en',
                                                                                    str(ex)))
        useful_synsets = {}
        for w_i, t_w in enumerate(trans.sentences[0].words):
            synsets = wn.synsets(trans.sentences[0].words[w_i])
            if len(synsets) == 0:
                continue
            eq_synset = self._compare_synsets(synsets, tokens)
            useful_synsets[t_w] = eq_synset
        scores = {}
        scores = {}
        if useful_synsets != None:
            for word in useful_synsets:
                if useful_synsets[word] is None:
                    continue
                temp_scores = self._swn.get_score(useful_synsets[word].name().split('.')[0].replace(' ',' '))
                for score in temp_scores:
                    if score['synset'] == useful_synsets[word]:
                        t_score = score['pos'] - score['neg']
                        f_score = 'neu'
                        if t_score > 0:
                            f_score = 'pos'
                        elif t_score < 0:
                            f_score = 'neg'
                        score['score'] = f_score
                        scores[word] = score
                        break
        g_score = 0.5

        for i in scores:
            n_pos = 0.0
            n_neg = 0.0
            for w in scores:
                if scores[w]['score'] == 'pos':
                    n_pos += 1.0
                elif scores[w]['score'] == 'neg':
                    n_neg += 1.0
            inter = interp1d([-1.0, 1.0], [0.0, 1.0])

            try:
                g_score = (n_pos - n_neg) / (n_pos + n_neg)
                g_score = float(inter(g_score))
            except:
                if n_pos == 0 and n_neg == 0:
                    g_score = 0.5

        if g_score > 0.5:  # Positive
            return [1, 0, 0]
        elif g_score < 0.5:  # Negative
            return [0, 0, 1]
        else:
            return [0, 1, 0]


    test_cases = [
        {
            'input': 'Odio ir al cine',
            'params': {'language': 'es'},
            'polarity': 'marl:Negative'

        },
        {
            'input': 'El cielo está nublado',
            'params': {'language': 'es'},
            'polarity': 'marl:Neutral'

        },
        {
            'input': 'Esta tarta está muy buena',
            'params': {'language': 'es'},
            'polarity': 'marl:Negative' # SURPRISINGLY!

        }
    ]
