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

from senpy.plugins import SentimentPlugin, SenpyPlugin
from senpy.models import Results, Entry, Sentiment

if sys.version_info[0] >= 3:
    unicode = str


class SentimentBasic(SentimentPlugin):
    '''
    Sentiment classifier using rule-based classification for Spanish. Based on english to spanish translation and SentiWordNet sentiment knowledge. This is a demo plugin that uses only some features from the TASS 2015 classifier. To use the entirely functional classifier you can use the service in: http://senpy.cluster.gsi.dit.upm.es.
    '''
    name = "sentiment-basic"
    author = "github.com/nachtkatze"
    version = "0.1.1"
    extra_params = {
        "language": {
            "aliases": ["language", "l"],
            "required": True,
            "options": ["en","es", "it", "fr", "auto"],
            "default": "auto"
        }
    }
    sentiword_path = "SentiWordNet_3.0.txt"
    pos_path = "unigram_spanish.pickle"
    maxPolarityValue = 1
    minPolarityValue = -1
    nltk_resources = ['punkt','wordnet', 'omw']

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
        data = {}
        sentences = nltk.sent_tokenize(text)
        for i, sentence in enumerate(sentences):
            sentence_ = {}
            words = nltk.word_tokenize(sentence)
            sentence_['sentence'] = sentence
            tokens_ = [w.lower() for w in words]
            sentence_['tokens'] = self._remove_punctuation(tokens_)
            data[i] = sentence_
        return data

    def _pos(self, tokens):
        for i in tokens:
            tokens[i]['tokens'] = self._pos_tagger.tag(tokens[i]['tokens'])
        return tokens

    def _compare_synsets(self, synsets, tokens, i):
        for synset in synsets:
            for word in tokens[i]['lemmas']:
                for lemma in tokens[i]['lemmas'][word]:
                    synset_ = lemma.synset() 
                    if synset == synset_:
                        return synset
        return None


    def analyse_entry(self, entry, params):
        language = params.get("language")
        text = entry.text
        tokens = self._tokenize(text)
        tokens = self._pos(tokens)
        sufixes = {'es':'spa','en':'eng','it':'ita','fr':'fra'}
        for i in tokens:
            tokens[i]['lemmas'] = {}
            for w in tokens[i]['tokens']:
                lemmas = wn.lemmas(w[0], lang=sufixes[language])
                if len(lemmas) == 0:
                    continue
                tokens[i]['lemmas'][w[0]] = lemmas
        if language == "en":
            trans = TextBlob(unicode(text))
        else:
            trans = TextBlob(unicode(text)).translate(from_lang=language,to='en')
        useful_synsets = {}
        for s_i, t_s in enumerate(trans.sentences):
            useful_synsets[s_i] = {}
            for w_i, t_w in enumerate(trans.sentences[s_i].words):
                synsets = wn.synsets(trans.sentences[s_i].words[w_i])
                if len(synsets) == 0:
                    continue
                eq_synset = self._compare_synsets(synsets, tokens, s_i)
                useful_synsets[s_i][t_w] = eq_synset
        scores = {}
        for i in tokens:
            scores[i] = {}
            if useful_synsets != None:   
                for word in useful_synsets[i]:
                    if useful_synsets[i][word] is None:
                        continue
                    temp_scores = self._swn.get_score(useful_synsets[i][word].name().split('.')[0].replace(' ',' '))
                    for score in temp_scores:
                        if score['synset'] == useful_synsets[i][word]:
                            t_score = score['pos'] - score['neg']
                            f_score = 'neu'
                            if t_score > 0:
                                f_score = 'pos'
                            elif t_score < 0:
                                f_score = 'neg'
                            score['score'] = f_score
                            scores[i][word] = score
                            break
        p = params.get("prefix", None)
        for i in scores:
            n_pos = 0.0
            n_neg = 0.0
            for w in scores[i]:
                if scores[i][w]['score'] == 'pos':
                    n_pos += 1.0
                elif scores[i][w]['score'] == 'neg':
                    n_neg += 1.0
            inter = interp1d([-1.0, 1.0], [0.0, 1.0])
            try:
                g_score = (n_pos - n_neg) / (n_pos + n_neg)
                g_score = float(inter(g_score))
            except:
                if n_pos == 0 and n_neg == 0:
                    g_score = 0.5
            if g_score >= 0.5:
                polarity = 'marl:Positive'
                polarity_value = 1
            elif g_score < 0.5:
                polarity = 'marl:Negative'
                polarity_value = -1
            else:
                polarity = 'marl:Neutral'
                polarity_value = 0
            opinion = Sentiment(id="Opinion0"+'_'+str(i),
                          marl__hasPolarity=polarity,
                          marl__polarityValue=polarity_value)

            opinion.prov(self)
            entry.sentiments.append(opinion)

        yield entry

    test_cases = [
        {
            'input': u'Odio ir al cine',
            'params': {'language': 'es'},
            'polarity': 'marl:Negative'

        },
        {
            'input': u'El cielo está nublado',
            'params': {'language': 'es'},
            'polarity': 'marl:Positive'

        },
        {
            'input': u'Esta tarta está muy buena',
            'params': {'language': 'es'},
            'polarity': 'marl:Negative'

        }
    ]
