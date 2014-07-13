#!/usr/bin/python
# -*- coding: utf-8 -*-
#    Copyright 2014 J. Fernando Sánchez Rada - Grupo de Sistemas Inteligentes
#                                                       DIT, UPM
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
'''
Simple Sentiment Analysis server for EUROSENTIMENT

This class shows how to use the nif_server module to create custom services.
'''
import config
import re
from flask import Flask
import random
from nif_server import *

app = Flask(__name__)

rgx = re.compile("(\w[\w']*\w|\w)", re.U)

def hard_analysis(params):
    response = basic_analysis(params)
    response["analysis"][0].update({ "marl:algorithm": "SimpleAlgorithm",
                                     "marl:minPolarityValue": -1,
                                     "marl:maxPolarityValue": 1})
    for i in response["entries"]:
        contextid = i["@id"]
        random.seed(str(params))
        polValue = 2*random.random()-1
        if polValue > 0:
            pol = "marl:Positive"
        elif polValue == 0:
            pol = "marl:Neutral"
        else:
            pol = "marl:Negative"
        i["opinions"] = [{"marl:polarityValue": polValue,
                          "marl:hasPolarity": pol

                          }]
        i["strings"] = []
        for m in rgx.finditer(i["nif:isString"]):
            i["strings"].append({
                "@id": "{}#char={},{}".format(contextid, m.start(), m.end()),
                "nif:beginIndex": m.start(),
                "nif:endIndex": m.end(),
                "nif:anchorOf": m.group(0)
            })

    return response

app.analyse = hard_analysis
app.register_blueprint(nif_server)

if __name__ == '__main__':
    app.debug = config.DEBUG
    app.run()
