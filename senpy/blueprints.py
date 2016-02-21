#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2014 J. Fernando Sánchez Rada - Grupo de Sistemas Inteligentes
# DIT, UPM
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
"""
Blueprints for Senpy
"""
from flask import Blueprint, request, current_app, render_template
from .models import Error, Response, Plugins
from future.utils import iteritems

import json
import logging

logger = logging.getLogger(__name__)

nif_blueprint = Blueprint("NIF Sentiment Analysis Server", __name__)
demo_blueprint = Blueprint("Demo of the service. It includes an HTML+Javascript playground to test senpy", __name__)

API_PARAMS = {
    "algorithm": {
        "aliases": ["algorithm", "a", "algo"],
        "required": False,
    },
    "inHeaders": {
        "aliases": ["inHeaders", "headers"],
        "required": True,
        "default": "0"
    },
    "prefix": {
        "@id": "prefix",
        "aliases": ["prefix", "p"],
        "required": True,
        "default": "",
    },
}

BASIC_PARAMS = {
    "algorithm": {
        "aliases": ["algorithm", "a", "algo"],
        "required": False,
    },
    "inHeaders": {
        "aliases": ["inHeaders", "headers"],
        "required": True,
        "default": "0"
    },
    "input": {
        "@id": "input",
        "aliases": ["i", "input"],
        "required": True,
        "help": "Input text"
    },
    "informat": {
        "@id": "informat",
        "aliases": ["f", "informat"],
        "required": False,
        "default": "text",
        "options": ["turtle", "text"],
    },
    "intype": {
        "@id": "intype",
        "aliases": ["intype", "t"],
        "required": False,
        "default": "direct",
        "options": ["direct", "url", "file"],
    },
    "outformat": {
        "@id": "outformat",
        "aliases": ["outformat", "o"],
        "default": "json-ld",
        "required": False,
        "options": ["json-ld"],
    },
    "language": {
        "@id": "language",
        "aliases": ["language", "l"],
        "required": False,
    },
    "prefix": {
        "@id": "prefix",
        "aliases": ["prefix", "p"],
        "required": True,
        "default": "",
    },
    "urischeme": {
        "@id": "urischeme",
        "aliases": ["urischeme", "u"],
        "required": False,
        "default": "RFC5147String",
        "options": "RFC5147String"
    },
}

def get_params(req, params=BASIC_PARAMS):
    if req.method == 'POST':
        indict = req.form
    elif req.method == 'GET':
        indict = req.args
    else:
        raise Error(message="Invalid data")

    outdict = {}
    wrong_params = {}
    for param, options in iteritems(params):
        if param[0] != "@":  # Exclude json-ld properties
            logger.debug("Param: %s - Options: %s", param, options)
            for alias in options["aliases"]:
                if alias in indict:
                    outdict[param] = indict[alias]
            if param not in outdict:
                if options.get("required", False) and "default" not in options:
                    wrong_params[param] = params[param]
                else:
                    if "default" in options:
                        outdict[param] = options["default"]
            else:
                if "options" in params[param] and \
                   outdict[param] not in params[param]["options"]:
                    wrong_params[param] = params[param]
    if wrong_params:
        message = Error(status=404,
                        message="Missing or invalid parameters",
                        parameters=outdict,
                        errors={param: error for param, error in
                                iteritems(wrong_params)})
        raise Error(message=message)
    return outdict


def basic_analysis(params):
    response = {"@context":
                [("http://demos.gsi.dit.upm.es/"
                  "eurosentiment/static/context.jsonld"),
                 {
                    "@base": "{}#".format(request.url.encode('utf-8'))
                  }
                 ],
                "analysis": [{"@type": "marl:SentimentAnalysis"}],
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


@demo_blueprint.route('/')
def index():
    return render_template("index.html")


@nif_blueprint.route('/', methods=['POST', 'GET'])
def api():
    try:
        params = get_params(request)
        algo = params.get("algorithm", None)
        specific_params = current_app.senpy.parameters(algo)
        logger.debug(
            "Specific params: %s", json.dumps(specific_params, indent=4))
        params.update(get_params(request, specific_params))
        response = current_app.senpy.analyse(**params)
        in_headers = params["inHeaders"] != "0"
        prefix = params["prefix"]
        return response.flask(in_headers=in_headers, prefix=prefix)
    except Error as ex:
        return ex.message.flask()


@nif_blueprint.route('/plugins/', methods=['POST', 'GET'])
def plugins():
    in_headers = get_params(request, API_PARAMS)["inHeaders"] != "0"
    sp = current_app.senpy
    dic = Plugins(plugins=list(sp.plugins.values()))
    return dic.flask(in_headers=in_headers)
    
@nif_blueprint.route('/plugins/<plugin>/', methods=['POST', 'GET'])
@nif_blueprint.route('/plugins/<plugin>/<action>', methods=['POST', 'GET'])
def plugin(plugin=None, action="list"):
    params = get_params(request, API_PARAMS)
    filt = {}
    sp = current_app.senpy
    plugs = sp.filter_plugins(name=plugin)
    if plugin == 'default' and sp.default_plugin:
        response = sp.default_plugin
        plugin = response.name
    elif plugin in sp.plugins:
        response = sp.plugins[plugin]
    else:
        return Error(message="Plugin not found", status=404).flask()
    if action == "list":
        in_headers = params["inHeaders"] != "0"
        prefix = params['prefix']
        return response.flask(in_headers=in_headers, prefix=prefix)
    method = "{}_plugin".format(action)
    if(hasattr(sp, method)):
        getattr(sp, method)(plugin)
        return Response(message="Ok").flask()
    else:
        return Error(message="action '{}' not allowed".format(action)).flask()

if __name__ == '__main__':
    import config

    app.register_blueprint(nif_blueprint)
    app.debug = config.DEBUG
    app.run(host='0.0.0.0', port=5000)
