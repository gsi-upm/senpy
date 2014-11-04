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

BASIC_PARAMS = {
    "algorithm": {"aliases": ["algorithm", "a", "algo"],
                  "required": False,
                  },
}

def get_params(req, params=BASIC_PARAMS):
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
        algo = get_params(request).get("algorithm", None)
        specific_params = current_app.senpy.parameters(algo)
        params = get_params(request, specific_params)
    except ValueError as ex:
        return ex.message
    response = current_app.senpy.analyse(**params)
    return jsonify(response)

@nif_blueprint.route("/default")
def default():
    return current_app.senpy.default_plugin
    #return plugins(action="list", plugin=current_app.senpy.default_algorithm)

@nif_blueprint.route('/plugins/', methods=['POST', 'GET'])
@nif_blueprint.route('/plugins/<plugin>', methods=['POST', 'GET'])
@nif_blueprint.route('/plugins/<plugin>/<action>', methods=['POST', 'GET'])
def plugins(plugin=None, action="list"):
    filt = {}
    if plugin:
        filt["name"] = plugin
    plugs = current_app.senpy.filter_plugins(**filt)
    if plugin and not plugs:
        return "Plugin not found", 400
    if action == "list":
        with_params = request.args.get("params", "") == "1"
        dic = {plug:plugs[plug].jsonable(with_params) for plug in plugs}
        return jsonify(dic)
    if action == "disable":
        current_app.senpy.disable_plugin(plugin)
        return "Ok"
    elif action == "enable":
        current_app.senpy.enable_plugin(plugin)
        return "Ok"
    elif action == "reload":
        current_app.senpy.reload_plugin(plugin)
        return "Ok"
    else:
        return "action '{}' not allowed".format(action), 400

if __name__ == '__main__':
    import config
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(nif_blueprint)
    app.debug = config.DEBUG
    app.run()
