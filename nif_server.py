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
'''
from flask import Blueprint, render_template, request, jsonify, current_app
import config
import json

nif_server = Blueprint("NIF Sentiment Analysis Server", __name__)

PARAMS = {"input": {"aliases": ["i", "input"],
                    "help": "Input text"
                    },
          "informat": {"aliases": ["f", "informat"],
                       "default": "text",
                       "options": ["turtle", "text"],
                       },
          "intype": {"aliases": ["intype", "t"],
                     "default": "direct",
                     "options": ["direct", "url", "file"],
                     },
          "outformat": {"aliases": ["outformat", "o"],
                        "default": "json-ld",
                        "options": ["json-ld"],
                        },
          "language": {"aliases": ["language", "l"],
                        "default": None,
                        "options": ["es", "en"],
                        },
          "urischeme": {"aliases": ["urischeme", "u"],
                        "default": "RFC5147String",
                        "options": "RFC5147String"
                        },
          }


def get_params(req):
    indict = None
    if req.method == 'POST':
        indict = req.form
    if req.method == 'GET':
        indict = req.args
    else:
        raise ValueError("Invalid data")

    outdict = {}
    missingParams = []
    for param, options in PARAMS.iteritems():
        for alias in options["aliases"]:
            if alias in indict:
                outdict[param] = indict[alias]
        if param not in outdict:
            if "default" in options:
                if options["default"]:
                    outdict[param] = options["default"]
            else:
                missingParams.append(param)
    if missingParams:
        message = {"status": "failed", "message": "Missing parameters"}
        message["parameters"] = {param:PARAMS[param] for param in missingParams}
        raise ValueError(json.dumps(message))
    return outdict

def basic_analysis(params):
    response = {"@context": "http://demos.gsi.dit.upm.es/eurosentiment/static/context.jsonld",
                "analysis": [{
                    "@type": "marl:SentimentAnalysis"
                }],
                "entries": []
                }
    if "language" in params:
        response["language"] = params["language"]
    for sentence in params["input"].split("."):
        response["entries"].append({
            "nif:isString": sentence
        })
    return response

@nif_server.route('/', methods=['POST', 'GET'])
def home(entries=None):
    try:
        params = get_params(request)
    except ValueError as ex:
        return ex.message
    response = current_app.analyse(params)
    return jsonify(response)

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(nif_server)
    app.debug = config.DEBUG
    app.run()
