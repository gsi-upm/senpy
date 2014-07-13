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
                    "required": True,
                    "help": "Input text"
                    },
          "informat": {"aliases": ["f", "informat"],
                       "required": False,
                       "default": "text",
                       "options": ["turtle", "text"],
                       },
          "intype": {"aliases": ["intype", "t"],
                     "required": False,
                     "default": "direct",
                     "options": ["direct", "url", "file"],
                     },
          "outformat": {"aliases": ["outformat", "o"],
                        "default": "json-ld",
                        "required": False,
                        "options": ["json-ld"],
                        },
          "language": {"aliases": ["language", "l"],
                       "required": False,
                       "options": ["es", "en"],
                       },
          "urischeme": {"aliases": ["urischeme", "u"],
                        "required": False,
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
    wrongParams = {}
    for param, options in PARAMS.iteritems():
        for alias in options["aliases"]:
            if alias in indict:
                outdict[param] = indict[alias]
        if param not in outdict:
            if options.get("required", False):
                wrongParams[param] = PARAMS[param]
            else:
                if "default" in options:
                    outdict[param] = options["default"]
        else:
            if "options" in PARAMS[param] and \
                outdict[param] not in PARAMS[param]["options"]:
                wrongParams[param] = PARAMS[param]
    if wrongParams:
        message = {"status": "failed", "message": "Missing or invalid parameters"}
        message["parameters"] = outdict
        message["errors"] = {param:error for param, error in wrongParams.iteritems()}
        raise ValueError(json.dumps(message))
    return outdict

def basic_analysis(params):
    response = {"@context": ["http://demos.gsi.dit.upm.es/eurosentiment/static/context.jsonld",
                             {
                                 "@base": "{}#".format(request.url.encode('utf-8'))
                             }
                             ],
                "analysis": [{
                    "@type": "marl:SentimentAnalysis"
                }],
                "entries": []
                }
    if "language" in params:
        response["language"] = params["language"]
    for idx, sentence in enumerate(params["input"].split(".")):
        response["entries"].append({
            "@id": "Sentence{}".format(idx),
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
