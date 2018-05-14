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
from flask import (Blueprint, request, current_app, render_template, url_for,
                   jsonify)
from .models import Error, Response, Help, Plugins, read_schema, dump_schema, Datasets
from . import api
from .version import __version__
from functools import wraps

import logging
import traceback
import json

logger = logging.getLogger(__name__)

api_blueprint = Blueprint("api", __name__)
demo_blueprint = Blueprint("demo", __name__, template_folder='templates')
ns_blueprint = Blueprint("ns", __name__)


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
    return render_template("index.html", version=__version__)


@api_blueprint.route('/contexts/<entity>.jsonld')
def context(entity="context"):
    context = Response._context
    context['@vocab'] = url_for('ns.index', _external=True)
    return jsonify({"@context": context})


@ns_blueprint.route('/')  # noqa: F811
def index():
    context = Response._context
    context['@vocab'] = url_for('.ns', _external=True)
    return jsonify({"@context": context})


@api_blueprint.route('/schemas/<schema>')
def schema(schema="definitions"):
    try:
        return dump_schema(read_schema(schema))
    except Exception as ex:  # Should be FileNotFoundError, but it's missing from py2
        return Error(message="Schema not found: {}".format(ex), status=404).flask()


def basic_api(f):
    default_params = {
        'inHeaders': False,
        'expanded-jsonld': False,
        'outformat': 'json-ld',
        'with_parameters': True,
    }

    @wraps(f)
    def decorated_function(*args, **kwargs):
        raw_params = get_params(request)
        logger.info('Getting request: {}'.format(raw_params))
        headers = {'X-ORIGINAL-PARAMS': json.dumps(raw_params)}
        params = default_params

        try:
            params = api.parse_params(raw_params, api.WEB_PARAMS, api.API_PARAMS)
            if hasattr(request, 'parameters'):
                request.parameters.update(params)
            else:
                request.parameters = params
            response = f(*args, **kwargs)
        except (Exception) as ex:
            if current_app.debug:
                raise
            if not isinstance(ex, Error):
                msg = "{}:\n\t{}".format(ex,
                                         traceback.format_exc())
                ex = Error(message=msg, status=500)
            logger.exception('Error returning analysis result')
            response = ex
            response.parameters = raw_params
            logger.error(ex)

        if 'parameters' in response and not params['with_parameters']:
            del response.parameters

        logger.info('Response: {}'.format(response))
        return response.flask(
            in_headers=params['inHeaders'],
            headers=headers,
            prefix=url_for('.api_root', _external=True),
            context_uri=url_for('api.context',
                                entity=type(response).__name__,
                                _external=True),
            outformat=params['outformat'],
            expanded=params['expanded-jsonld'])

    return decorated_function


@api_blueprint.route('/', methods=['POST', 'GET'])
@basic_api
def api_root():
    if request.parameters['help']:
        dic = dict(api.API_PARAMS, **api.NIF_PARAMS)
        response = Help(valid_parameters=dic)
        return response
    req = api.parse_call(request.parameters)
    return current_app.senpy.analyse(req)


@api_blueprint.route('/evaluate/', methods=['POST', 'GET'])
@basic_api
def evaluate():
    if request.parameters['help']:
        dic = dict(api.EVAL_PARAMS)
        response = Help(parameters=dic)
        return response
    else:
        params = api.parse_params(request.parameters, api.EVAL_PARAMS)
        response = current_app.senpy.evaluate(params)
        return response


@api_blueprint.route('/plugins/', methods=['POST', 'GET'])
@basic_api
def plugins():
    sp = current_app.senpy
    params = api.parse_params(request.parameters, api.PLUGINS_PARAMS)
    ptype = params.get('plugin_type')
    plugins = list(sp.plugins(plugin_type=ptype))
    dic = Plugins(plugins=plugins)
    return dic


@api_blueprint.route('/plugins/<plugin>/', methods=['POST', 'GET'])
@basic_api
def plugin(plugin=None):
    sp = current_app.senpy
    return sp.get_plugin(plugin)


@api_blueprint.route('/datasets/', methods=['POST', 'GET'])
@basic_api
def datasets():
    sp = current_app.senpy
    datasets = sp.datasets
    dic = Datasets(datasets=list(datasets.values()))
    return dic
