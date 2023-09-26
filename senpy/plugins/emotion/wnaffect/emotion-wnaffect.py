# -*- coding: utf-8 -*-
from __future__ import division
import re
import nltk
import os
import string
import xml.etree.ElementTree as ET
from nltk.corpus import stopwords
from nltk.corpus import WordNetCorpusReader
from nltk.stem import wordnet
from emotion import Emotion as Emo
from senpy.plugins import EmotionPlugin, AnalysisPlugin, ShelfMixin
from senpy.models import Results, EmotionSet, Entry, Emotion


class WNAffect(EmotionPlugin, ShelfMixin):
    '''
    Emotion classifier using WordNet-Affect to calculate the percentage
    of each emotion. This plugin classifies among 6 emotions: anger,fear,disgust,joy,sadness
    or neutral. The only available language is English (en)
    '''
    name = 'emotion-wnaffect'
    author = ["@icorcuera", "@balkian"]
    version = '0.2'
    extra_params = {
      'language': {
          "@id": 'lang_wnaffect',
          'description': 'language of the input',
          'aliases': ['language', 'l'],
          'required': True,
          'options': ['en',]
        }
    }
    synsets_path = "a-synsets.xml"
    hierarchy_path = "a-hierarchy.xml"
    wn16_path = "wordnet1.6/dict"
    onyx__usesEmotionModel = "emoml:big6"
    nltk_resources = ['stopwords', 'averaged_perceptron_tagger', 'wordnet']

    def _load_synsets(self, synsets_path):
        """Returns a dictionary POS tag -> synset offset -> emotion (str -> int -> str)."""
        tree = ET.parse(synsets_path)
        root = tree.getroot()
        pos_map = {"noun": "NN", "adj": "JJ", "verb": "VB", "adv": "RB"}

        synsets = {}
        for pos in ["noun", "adj", "verb", "adv"]:
            tag = pos_map[pos]
            synsets[tag] = {}
            for elem in root.findall(
                    ".//{0}-syn-list//{0}-syn".format(pos, pos)):
                offset = int(elem.get("id")[2:])
                if not offset: continue
                if elem.get("categ"):
                    synsets[tag][offset] = Emo.emotions[elem.get(
                        "categ")] if elem.get(
                            "categ") in Emo.emotions else None
                elif elem.get("noun-id"):
                    synsets[tag][offset] = synsets[pos_map["noun"]][int(
                        elem.get("noun-id")[2:])]
        return synsets

    def _load_emotions(self, hierarchy_path):
        """Loads the hierarchy of emotions from the WordNet-Affect xml."""

        tree = ET.parse(hierarchy_path)
        root = tree.getroot()
        for elem in root.findall("categ"):
            name = elem.get("name")
            if name == "root":
                Emo.emotions["root"] = Emo("root")
            else:
                Emo.emotions[name] = Emo(name, elem.get("isa"))

    def activate(self, *args, **kwargs):

        self._stopwords = stopwords.words('english')
        self._wnlemma = wordnet.WordNetLemmatizer()
        self._syntactics = {'N': 'n', 'V': 'v', 'J': 'a', 'S': 's', 'R': 'r'}
        local_path = os.environ.get("SENPY_DATA")
        self._categories = {
            'anger': [
                'general-dislike',
            ],
            'fear': [
                'negative-fear',
            ],
            'disgust': [
                'shame',
            ],
            'joy':
            ['gratitude', 'affective', 'enthusiasm', 'love', 'joy', 'liking'],
            'sadness': [
                'ingrattitude', 'daze', 'humility', 'compassion', 'despair',
                'anxiety', 'sadness'
            ]
        }

        self._wnaffect_mappings = {
            'anger': 'anger',
            'fear': 'negative-fear',
            'disgust': 'disgust',
            'joy': 'joy',
            'sadness': 'sadness'
        }

        self._load_emotions(self.find_file(self.hierarchy_path))

        if 'total_synsets' not in self.sh:
            total_synsets = self._load_synsets(self.find_file(self.synsets_path))
            self.sh['total_synsets'] = total_synsets

        self._total_synsets = self.sh['total_synsets']

        self._wn16_path = self.wn16_path
        self._wn16 = WordNetCorpusReader(self.find_file(self._wn16_path), nltk.data.find(self.find_file(self._wn16_path)))


    def deactivate(self, *args, **kwargs):
        self.save(ignore_errors=True)

    def _my_preprocessor(self, text):

        regHttp = re.compile(
            '(http://)[a-zA-Z0-9]*.[a-zA-Z0-9/]*(.[a-zA-Z0-9]*)?')
        regHttps = re.compile(
            '(https://)[a-zA-Z0-9]*.[a-zA-Z0-9/]*(.[a-zA-Z0-9]*)?')
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

    def _extract_ngrams(self, text):

        unigrams_lemmas = []
        pos_tagged = []
        unigrams_words = []
        tokens = text.split()
        for token in nltk.pos_tag(tokens):
            unigrams_words.append(token[0])
            pos_tagged.append(token[1])
            if token[1][0] in self._syntactics.keys():
                unigrams_lemmas.append(
                    self._wnlemma.lemmatize(token[0], self._syntactics[token[1]
                                                                       [0]]))
            else:
                unigrams_lemmas.append(token[0])

        return unigrams_words, unigrams_lemmas, pos_tagged

    def _find_ngrams(self, input_list, n):
        return zip(*[input_list[i:] for i in range(n)])

    def _clean_pos(self, pos_tagged):

        pos_tags = {
            'NN': 'NN',
            'NNP': 'NN',
            'NNP-LOC': 'NN',
            'NNS': 'NN',
            'JJ': 'JJ',
            'JJR': 'JJ',
            'JJS': 'JJ',
            'RB': 'RB',
            'RBR': 'RB',
            'RBS': 'RB',
            'VB': 'VB',
            'VBD': 'VB',
            'VGB': 'VB',
            'VBN': 'VB',
            'VBP': 'VB',
            'VBZ': 'VB'
        }

        for i in range(len(pos_tagged)):
            if pos_tagged[i] in pos_tags:
                pos_tagged[i] = pos_tags[pos_tagged[i]]
        return pos_tagged

    def _extract_features(self, text):

        feature_set = {k: 0 for k in self._categories}
        ngrams_words, ngrams_lemmas, pos_tagged = self._extract_ngrams(text)
        matches = 0
        pos_tagged = self._clean_pos(pos_tagged)

        tag_wn = {
            'NN': self._wn16.NOUN,
            'JJ': self._wn16.ADJ,
            'VB': self._wn16.VERB,
            'RB': self._wn16.ADV
        }
        for i in range(len(pos_tagged)):
            if pos_tagged[i] in tag_wn:
                synsets = self._wn16.synsets(ngrams_words[i],
                                             tag_wn[pos_tagged[i]])
                if synsets:
                    offset = synsets[0].offset()
                    if offset in self._total_synsets[pos_tagged[i]]:
                        if self._total_synsets[pos_tagged[i]][offset] is None:
                            continue
                        else:
                            emotion = self._total_synsets[pos_tagged[i]][
                                offset].get_level(5).name
                            matches += 1
                            for i in self._categories:
                                if emotion in self._categories[i]:
                                    feature_set[i] += 1
        if matches == 0:
            matches = 1

        for i in feature_set:
            feature_set[i] = (feature_set[i] / matches)

        return feature_set

    def analyse_entry(self, entry, activity):
        params = activity.params

        text_input = entry['nif:isString']

        text = self._my_preprocessor(text_input)

        feature_text = self._extract_features(text)

        emotionSet = EmotionSet(id="Emotions0")
        emotions = emotionSet.onyx__hasEmotion

        for i in feature_text:
            emotions.append(
                Emotion(
                    onyx__hasEmotionCategory=self._wnaffect_mappings[i],
                    onyx__hasEmotionIntensity=feature_text[i]))

        entry.emotions = [emotionSet]

        yield entry


    def test(self, *args, **kwargs):
        results = list()
        params = {'algo': 'emotion-wnaffect', 
                  'intype': 'direct', 
                  'expanded-jsonld': 0, 
                  'informat': 'text', 
                  'prefix': '', 
                  'plugin_type': 'analysisPlugin', 
                  'urischeme': 'RFC5147String', 
                  'outformat': 'json-ld', 
                  'i': 'Hello World', 
                  'input': 'Hello World', 
                  'conversion': 'full', 
                  'language': 'en',
                  'algorithm': 'emotion-wnaffect'}
        
        self.activate()
        texts = {'I hate you': 'anger',
                 'i am sad': 'sadness',
                 'i am happy with my marks': 'joy',
                 'This movie is scary': 'negative-fear'}

        for text in texts:
            response = next(self.analyse_entry(Entry(nif__isString=text),
                                               self.activity(params)))
            expected = texts[text]
            emotionSet = response.emotions[0]
            max_emotion = max(emotionSet['onyx:hasEmotion'], key=lambda x: x['onyx:hasEmotionIntensity'])
            assert max_emotion['onyx:hasEmotionCategory'] == expected
