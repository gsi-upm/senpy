# -*- coding: utf-8 -*-

import re
import nltk
import csv
import sys
import os
import unicodedata
import string
import xml.etree.ElementTree as ET
import math

from sklearn.svm import LinearSVC
from sklearn.feature_extraction import DictVectorizer

from nltk import bigrams
from nltk import trigrams
from nltk.corpus import stopwords

from pattern.en import parse as parse_en
from pattern.es import parse as parse_es
from senpy.plugins import SentimentPlugin, SenpyPlugin
from senpy.models import Results, EmotionSet, Entry, Emotion


class ANEW(SentimentPlugin):
    description = "This plugin consists on an emotion classifier using ANEW lexicon dictionary to calculate VAD (valence-arousal-dominance) of the sentence and determinate which emotion is closer to this value. Each emotion has a centroid, calculated according to this article: http://www.aclweb.org/anthology/W10-0208. The plugin is going to look for the words in the sentence that appear in the ANEW dictionary and calculate the average VAD score for the sentence. Once this score is calculated, it is going to seek the emotion that is closest to this value."
    author = "@icorcuera"
    version = "0.5.1"
    name = "emotion-anew"

    extra_params = {
        "language": {
            "aliases": ["language", "l"],
            "required": True,
            "options": ["es","en"],
            "default": "en"
        }
    }

    anew_path_es = "Dictionary/Redondo(2007).csv"
    anew_path_en = "Dictionary/ANEW2010All.txt"
    centroids = {
        "anger": {
            "A": 6.95,
            "D": 5.1,
            "V": 2.7
        },
        "disgust": {
            "A": 5.3,
            "D": 8.05,
            "V": 2.7
        },
        "fear": {
            "A": 6.5,
            "D": 3.6,
            "V": 3.2
        },
        "joy": {
            "A": 7.22,
            "D": 6.28,
            "V": 8.6
        },
        "sadness": {
            "A": 5.21,
            "D": 2.82,
            "V": 2.21
        }
    }
    emotions_ontology = {
        "anger": "http://gsi.dit.upm.es/ontologies/wnaffect/ns#anger",
        "disgust": "http://gsi.dit.upm.es/ontologies/wnaffect/ns#disgust",
        "fear": "http://gsi.dit.upm.es/ontologies/wnaffect/ns#negative-fear",
        "joy": "http://gsi.dit.upm.es/ontologies/wnaffect/ns#joy",
        "neutral": "http://gsi.dit.upm.es/ontologies/wnaffect/ns#neutral-emotion",
        "sadness": "http://gsi.dit.upm.es/ontologies/wnaffect/ns#sadness"
    }
    onyx__usesEmotionModel = "emoml:big6"
    nltk_resources = ['stopwords']

    def activate(self, *args, **kwargs):
        self._stopwords = stopwords.words('english')
        dictionary={}
        dictionary['es'] = {}
        with self.open(self.anew_path_es,'r') as tabfile:
            reader = csv.reader(tabfile, delimiter='\t')
            for row in reader:
                dictionary['es'][row[2]]={}
                dictionary['es'][row[2]]['V']=row[3]
                dictionary['es'][row[2]]['A']=row[5]
                dictionary['es'][row[2]]['D']=row[7]
        dictionary['en'] = {}
        with self.open(self.anew_path_en,'r') as tabfile:
            reader = csv.reader(tabfile, delimiter='\t')
            for row in reader:
                dictionary['en'][row[0]]={}
                dictionary['en'][row[0]]['V']=row[2]
                dictionary['en'][row[0]]['A']=row[4]
                dictionary['en'][row[0]]['D']=row[6]
        self._dictionary = dictionary

    def _my_preprocessor(self, text):

        regHttp = re.compile('(http://)[a-zA-Z0-9]*.[a-zA-Z0-9/]*(.[a-zA-Z0-9]*)?')
        regHttps = re.compile('(https://)[a-zA-Z0-9]*.[a-zA-Z0-9/]*(.[a-zA-Z0-9]*)?')
        regAt = re.compile('@([a-zA-Z0-9]*[*_/&%#@$]*)*[a-zA-Z0-9]*')
        text = re.sub(regHttp, '', text)
        text = re.sub(regAt, '', text)
        text = re.sub('RT : ', '', text)
        text = re.sub(regHttps, '', text)
        text = re.sub('[0-9]', '', text)
        text = self._delete_punctuation(text)
        return text

    def _delete_punctuation(self, text):

        exclude = set(string.punctuation)
        s = ''.join(ch for ch in text if ch not in exclude)
        return s

    def _extract_ngrams(self, text, lang):

        unigrams_lemmas = []
        unigrams_words = []
        pos_tagged = []
        if lang == 'es':
            sentences = parse_es(text,lemmata=True).split()
        else:
            sentences = parse_en(text,lemmata=True).split()

        for sentence in sentences:
            for token in sentence:
                if token[0].lower() not in self._stopwords:
                    unigrams_words.append(token[0].lower())
                    unigrams_lemmas.append(token[4])
                    pos_tagged.append(token[1])

        return unigrams_lemmas,unigrams_words,pos_tagged

    def _find_ngrams(self, input_list, n):
        return zip(*[input_list[i:] for i in range(n)])

    def _emotion_calculate(self, VAD):
        emotion=''
        value=10000000000000000000000.0
        for state in self.centroids:
            valence=VAD[0]-self.centroids[state]['V']
            arousal=VAD[1]-self.centroids[state]['A']
            dominance=VAD[2]-self.centroids[state]['D']
            new_value=math.sqrt((valence*valence)+(arousal*arousal)+(dominance*dominance))
            if new_value < value:
                value=new_value
                emotion=state
        return emotion

    def _extract_features(self, tweet,dictionary,lang):
        feature_set={}
        ngrams_lemmas,ngrams_words,pos_tagged = self._extract_ngrams(tweet,lang)
        pos_tags={'NN':'NN', 'NNS':'NN', 'JJ':'JJ', 'JJR':'JJ', 'JJS':'JJ', 'RB':'RB', 'RBR':'RB',
         'RBS':'RB', 'VB':'VB', 'VBD':'VB', 'VGB':'VB', 'VBN':'VB', 'VBP':'VB', 'VBZ':'VB'}
        totalVAD=[0,0,0]
        matches=0
        for word in range(len(ngrams_lemmas)):
            VAD=[]
            if ngrams_lemmas[word] in dictionary:
                matches+=1
                totalVAD = [totalVAD[0]+float(dictionary[ngrams_lemmas[word]]['V']),
                            totalVAD[1]+float(dictionary[ngrams_lemmas[word]]['A']),
                            totalVAD[2]+float(dictionary[ngrams_lemmas[word]]['D'])]
            elif ngrams_words[word] in dictionary:
                matches+=1
                totalVAD = [totalVAD[0]+float(dictionary[ngrams_words[word]]['V']),
                            totalVAD[1]+float(dictionary[ngrams_words[word]]['A']),
                            totalVAD[2]+float(dictionary[ngrams_words[word]]['D'])]
        if matches==0:
            emotion='neutral'
        else:
            totalVAD=[totalVAD[0]/matches,totalVAD[1]/matches,totalVAD[2]/matches]
            emotion=self._emotion_calculate(totalVAD)
        feature_set['emotion']=emotion
        feature_set['V']=totalVAD[0]
        feature_set['A']=totalVAD[1]
        feature_set['D']=totalVAD[2]
        return feature_set

    def analyse_entry(self, entry, params):

        text_input = entry.text

        text = self._my_preprocessor(text_input)
        dictionary = self._dictionary[params['language']]

        feature_set=self._extract_features(text, dictionary, params['language'])

        emotions = EmotionSet()
        emotions.id = "Emotions0"

        emotion1 = Emotion(id="Emotion0")
        emotion1["onyx:hasEmotionCategory"] = self.emotions_ontology[feature_set['emotion']]
        emotion1["http://www.gsi.dit.upm.es/ontologies/onyx/vocabularies/anew/ns#valence"] = feature_set['V']
        emotion1["http://www.gsi.dit.upm.es/ontologies/onyx/vocabularies/anew/ns#arousal"] = feature_set['A']
        emotion1["http://www.gsi.dit.upm.es/ontologies/onyx/vocabularies/anew/ns#dominance"] = feature_set['D']

        emotion1.prov(self)
        emotions.prov(self)

        emotions.onyx__hasEmotion.append(emotion1)
        entry.emotions = [emotions, ]

        yield entry

    ontology = "http://gsi.dit.upm.es/ontologies/wnaffect/ns#"
    test_cases = [
        {
            'input': 'I hate you',
            'expected': {
                'emotions': [{
                    'onyx:hasEmotion': [{
                        'onyx:hasEmotionCategory': ontology + 'anger',
                    }]
                }]
            }
        }, {
            'input': 'i am sad',
            'expected': {
                'emotions': [{
                    'onyx:hasEmotion': [{
                        'onyx:hasEmotionCategory': ontology + 'sadness',
                    }]
                }]
            }
        }, {
            'input': 'i am happy with my marks',
            'expected': {
                'emotions': [{
                    'onyx:hasEmotion': [{
                        'onyx:hasEmotionCategory': ontology + 'joy',
                    }]
                }]
            }
        }, {
            'input': 'This movie is scary',
            'expected': {
                'emotions': [{
                    'onyx:hasEmotion': [{
                        'onyx:hasEmotionCategory': ontology + 'negative-fear',
                    }]
                }]
            }
        }, {
            'input': 'this cake is disgusting' ,
            'expected': {
                'emotions': [{
                    'onyx:hasEmotion': [{
                        'onyx:hasEmotionCategory': ontology + 'negative-fear',
                    }]
                }]
            }
        }
    ]
