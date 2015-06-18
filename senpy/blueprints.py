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
from flask import Blueprint, request, current_app
from .models import Error, Response, Leaf

import json
import logging

logger = logging.getLogger(__name__)


nif_blueprint = Blueprint("NIF Sentiment Analysis Server", __name__)

BASIC_PARAMS = {
    "algorithm": {
        "aliases": ["algorithm", "a", "algo"],
        "required": False,
    },
    "inHeaders": {
        "aliases": ["inHeaders", "headers"],
        "required": True,
        "default": "0"
    }
}

LIST_PARAMS = {
    "params": {
        "aliases": ["params", "with_params"],
        "required": False,
        "default": "0"
    },
}


def get_params(req, params=BASIC_PARAMS):
    if req.method == 'POST':
        indict = req.form
    elif req.method == 'GET':
        indict = req.args
    else:
        raise ValueError("Invalid data")

    outdict = {}
    wrong_params = {}
    for param, options in params.iteritems():
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
        message = Error({"status": 404,
                         "message": "Missing or invalid parameters",
                         "parameters": outdict,
                         "errors": {param: error for param, error in
                                    wrong_params.iteritems()}
                         })
        raise ValueError(message)
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


@nif_blueprint.route('/', methods=['POST', 'GET'])
def home():
    try:
        params = get_params(request)
        algo = params.get("algorithm", None)
        specific_params = current_app.senpy.parameters(algo)
        logger.debug(
            "Specific params: %s", json.dumps(specific_params, indent=4))
        params.update(get_params(request, specific_params))
        response = current_app.senpy.analyse(**params)
        in_headers = params["inHeaders"] != "0"
        return response.flask(in_headers=in_headers)
    except ValueError as ex:
        return ex.message.flask()


@nif_blueprint.route("/default")
def default():
    # return current_app.senpy.default_plugin
    plug = current_app.senpy.default_plugin
    if plug:
        return plugins(action="list", plugin=plug.name)
    else:
        error = Error(status=404, message="No plugins found")
        return error.flask()


@nif_blueprint.route('/plugins/', methods=['POST', 'GET'])
@nif_blueprint.route('/plugins/<plugin>', methods=['POST', 'GET'])
@nif_blueprint.route('/plugins/<plugin>/<action>', methods=['POST', 'GET'])
def plugins(plugin=None, action="list"):
    filt = {}
    sp = current_app.senpy
    if plugin:
        filt["name"] = plugin
    plugs = sp.filter_plugins(**filt)
    if plugin and not plugs:
        return "Plugin not found", 400
    if action == "list":
        with_params = get_params(request, LIST_PARAMS)["params"] == "1"
        in_headers = get_params(request, BASIC_PARAMS)["inHeaders"] != "0"
        if plugin:
            dic = plugs[plugin]
        else:
            dic = Response(
                    {plug: plugs[plug].jsonld(with_params) for plug in plugs},
                    frame={})
        return dic.flask(in_headers=in_headers)
    method = "{}_plugin".format(action)
    if(hasattr(sp, method)):
        getattr(sp, method)(plugin)
        return Leaf(message="Ok").flask()
    else:
        return Error("action '{}' not allowed".format(action)).flask()


if __name__ == '__main__':
    import config
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(nif_blueprint)
    app.debug = config.DEBUG
    app.run()
