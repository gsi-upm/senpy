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
Simple Sentiment Analysis server
'''
from flask import Blueprint, render_template, request, jsonify, current_app
import json

nif_blueprint = Blueprint("NIF Sentiment Analysis Server", __name__)

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
          "algorithm": {"aliases": ["algorithm", "a", "algo"],
                        "required": False,
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

def get_algorithm(req):
    return get_params(req, params={"algorithm": PARAMS["algorithm"]})

def get_params(req, params=PARAMS):
    indict = None
    if req.method == 'POST':
        indict = req.form
    elif req.method == 'GET':
        indict = req.args
    else:
        raise ValueError("Invalid data")

    outdict = {}
    wrongParams = {}
    for param, options in params.iteritems():
        for alias in options["aliases"]:
            if alias in indict:
                outdict[param] = indict[alias]
        if param not in outdict:
            if options.get("required", False):
                wrongParams[param] = params[param]
            else:
                if "default" in options:
                    outdict[param] = options["default"]
        else:
            if "options" in params[param] and \
                outdict[param] not in params[param]["options"]:
                wrongParams[param] = params[param]
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

@nif_blueprint.route('/', methods=['POST', 'GET'])
def home(entries=None):
    try:
        algo = get_algorithm(request)["algorithm"]
        specific_params = PARAMS.copy()
        specific_params.update(current_app.senpy.parameters(algo))
        params = get_params(request, specific_params)
    except ValueError as ex:
        return ex.message
    response = current_app.senpy.analyse(**params)
    return jsonify(response)

@nif_blueprint.route('/plugins/', methods=['POST', 'GET'])
@nif_blueprint.route('/plugins/<plugin>', methods=['POST', 'GET'])
@nif_blueprint.route('/plugins/<plugin>/<action>', methods=['POST', 'GET'])
def plugins(plugin=None, action="list"):
    print current_app.senpy.plugins.keys()
    if plugin:
        plugs = {plugin:current_app.senpy.plugins[plugin]}
    else:
        plugs = current_app.senpy.plugins
    if action == "list":
        dic = {plug:plugs[plug].jsonable(True) for plug in plugs}
        return jsonify(dic)
    elif action == "disable":
        plugs[plugin].enabled = False
        return "Ok"
    elif action == "enable":
        plugs[plugin].enabled = True
        return "Ok"
    else:
        return "action '{}' not allowed".format(action), 404

if __name__ == '__main__':
    import config
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(nif_blueprint)
    app.debug = config.DEBUG
    app.run()
