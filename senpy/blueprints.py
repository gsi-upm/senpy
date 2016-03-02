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
from .api import NIF_PARAMS, WEB_PARAMS, parse_params
from functools import wraps

import json
import logging

logger = logging.getLogger(__name__)

api_blueprint = Blueprint("api", __name__)
demo_blueprint = Blueprint("demo", __name__)

def get_params(req):
    if req.method == 'POST':
        indict = req.form.to_dict(flat=True)
    elif req.method == 'GET':
        indict = req.args.to_dict(flat=True)
    else:
        raise Error(message="Invalid data")
    return indict


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
        raw_params = get_params(request)
        web_params = parse_params(raw_params, spec=WEB_PARAMS)

        if hasattr(request, 'params'):
            request.params.update(raw_params)
        else:
            request.params = raw_params
        try:
            response = f(*args, **kwargs)
        except Error as ex:
            response = ex
        in_headers = web_params["inHeaders"] != "0"
        headers = {'X-ORIGINAL-PARAMS': raw_params}
        return response.flask(in_headers=in_headers,
                              headers=headers,
                              context_uri=url_for('api.context', entity=type(response).__name__,
                                                  _external=True))
    return decorated_function
    
@api_blueprint.route('/', methods=['POST', 'GET'])
@basic_api
def api():
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
