#!/usr/bin/env python
"""
Author : Jaganadh Gopinadhan <jaganadhg@gmail.com>
Copywright (C) : Jaganadh Gopinadhan

 Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at
 
      http://www.apache.org/licenses/LICENSE-2.0
 
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
"""

import sys,os
import re

from nltk.corpus import wordnet

class SentiWordNet(object):
    """
    Interface to SentiWordNet
    """
    def __init__(self,swn_file):
        """
        """
        self.swn_file = swn_file
        self.pos_synset = self.__parse_swn_file()

    def __parse_swn_file(self):
        """
        Parse the SentiWordNet file and populate the POS and SynsetID hash
        """
        pos_synset_hash = {}
        swn_data = open(self.swn_file,'r').readlines()
        head_less_swn_data = filter((lambda line: not re.search(r"^\s*#",\
        line)), swn_data)

        for data in head_less_swn_data:
            fields = data.strip().split("\t")
            try:
                pos,syn_set_id,pos_score,neg_score,syn_set_score,\
                gloss = fields
            except:
                print("Found data without all details")
                pass

            if pos and syn_set_score:
                pos_synset_hash[(pos,int(syn_set_id))] = (float(pos_score),\
                float(neg_score))

        return pos_synset_hash

    def get_score(self,word,pos=None):
        """
        Get score for a given word/word pos combination
        """
        senti_scores = []
        synsets = wordnet.synsets(word,pos)
        for synset in synsets:
            if (synset.pos(), synset.offset()) in self.pos_synset:
                pos_val, neg_val = self.pos_synset[(synset.pos(), synset.offset())]
                senti_scores.append({"pos":pos_val,"neg":neg_val,\
                "obj": 1.0 - (pos_val - neg_val),'synset':synset})

        return senti_scores
