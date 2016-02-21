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
from flask import Blueprint, request, current_app, render_template, url_for, jsonify
from .models import Error, Response, Plugins, read_schema
from future.utils import iteritems
from functools import wraps

import json
import logging

logger = logging.getLogger(__name__)

api_blueprint = Blueprint("api", __name__)
demo_blueprint = Blueprint("demo", __name__)

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

NIF_PARAMS = {
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

def update_params(req, params=NIF_PARAMS):
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
        raise message
    if hasattr(request, 'params'):
        request.params.update(outdict)
    else:
        request.params = outdict
    return outdict


@demo_blueprint.route('/')
def index():
    return render_template("index.html")

@api_blueprint.route('/contexts/<entity>.jsonld')
def context(entity="context"):
    return jsonify({"@context": Response.context})

@api_blueprint.route('/schemas/<schema>')
def schema(schema="definitions"):
    try:
        return jsonify(read_schema(schema))
    except Exception: # Should be FileNotFoundError, but it's missing from py2
        return Error(message="Schema not found", status=404).flask()

def basic_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print('Getting request:')
        print(request)
        update_params(request, params=API_PARAMS)
        print('Params: %s' % request.params)
        try:
            response = f(*args, **kwargs)
        except Error as ex:
            response = ex
        in_headers = request.params["inHeaders"] != "0"
        prefix = request.params["prefix"]
        headers = {'X-ORIGINAL-PARAMS': request.params}
        return response.flask(in_headers=in_headers,
                              prefix=prefix,
                              headers=headers,
                              context_uri=url_for('api.context', entity=type(response).__name__,
                                                  _external=True))
    return decorated_function
    
@api_blueprint.route('/', methods=['POST', 'GET'])
@basic_api
def api():
    algo = request.params.get("algorithm", None)
    specific_params = current_app.senpy.parameters(algo)
    update_params(request, params=NIF_PARAMS)
    logger.debug("Specific params: %s", json.dumps(specific_params, indent=4))
    update_params(request, specific_params)
    response = current_app.senpy.analyse(**request.params)
    return response


@api_blueprint.route('/plugins/', methods=['POST', 'GET'])
@basic_api
def plugins():
    sp = current_app.senpy
    dic = Plugins(plugins=list(sp.plugins.values()))
    return dic
    
@api_blueprint.route('/plugins/<plugin>/', methods=['POST', 'GET'])
@api_blueprint.route('/plugins/<plugin>/<action>', methods=['POST', 'GET'])
@basic_api
def plugin(plugin=None, action="list"):
    filt = {}
    sp = current_app.senpy
    plugs = sp.filter_plugins(name=plugin)
    if plugin == 'default' and sp.default_plugin:
        response = sp.default_plugin
        plugin = response.name
    elif plugin in sp.plugins:
        response = sp.plugins[plugin]
    else:
        return Error(message="Plugin not found", status=404)
    if action == "list":
        return response
    method = "{}_plugin".format(action)
    if(hasattr(sp, method)):
        getattr(sp, method)(plugin)
        return Response(message="Ok")
    else:
        return Error(message="action '{}' not allowed".format(action))

if __name__ == '__main__':
    import config

    app.register_blueprint(api_blueprint)
    app.debug = config.DEBUG
    app.run(host='0.0.0.0', port=5000)
