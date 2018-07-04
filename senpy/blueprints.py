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
                   jsonify, redirect)
from .models import Error, Response, Help, Plugins, read_schema, dump_schema, Datasets
from . import api
from .version import __version__
from functools import wraps

import logging
import json
import base64

logger = logging.getLogger(__name__)

api_blueprint = Blueprint("api", __name__)
demo_blueprint = Blueprint("demo", __name__, template_folder='templates')
ns_blueprint = Blueprint("ns", __name__)

_mimetypes_r = {'json-ld': ['application/ld+json'],
                'turtle': ['text/turtle'],
                'ntriples': ['application/n-triples'],
                'text': ['text/plain']}

MIMETYPES = {}

for k, vs in _mimetypes_r.items():
    for v in vs:
        if v in MIMETYPES:
            raise Exception('MIMETYPE {} specified for two formats: {} and {}'.format(v,
                                                                                      v,
                                                                                      MIMETYPES[v]))
        MIMETYPES[v] = k

DEFAULT_MIMETYPE = 'application/ld+json'
DEFAULT_FORMAT = 'json-ld'


def get_params(req):
    if req.method == 'POST':
        indict = req.form.to_dict(flat=True)
    elif req.method == 'GET':
        indict = req.args.to_dict(flat=True)
    else:
        raise Error(message="Invalid data")
    return indict


def encoded_url(url=None, base=None):
    code = ''
    if not url:
        if request.method == 'GET':
            url = request.full_path[1:]  # Remove the first slash
        else:
            hash(frozenset(request.form.params().items()))
            code = 'hash:{}'.format(hash)

    code = code or base64.urlsafe_b64encode(url.encode()).decode()

    if base:
        return base + code
    return url_for('api.decode', code=code, _external=True)


def decoded_url(code, base=None):
    if code.startswith('hash:'):
        raise Exception('Can not decode a URL for a POST request')
    base = base or request.url_root
    path = base64.urlsafe_b64decode(code.encode()).decode()
    return base + path


@demo_blueprint.route('/')
def index():
    ev = str(get_params(request).get('evaluation', False))
    evaluation_enabled = ev.lower() not in ['false', 'no', 'none']

    return render_template("index.html",
                           evaluation=evaluation_enabled,
                           version=__version__)


@api_blueprint.route('/contexts/<entity>.jsonld')
def context(entity="context"):
    context = Response._context
    context['@vocab'] = url_for('ns.index', _external=True)
    context['endpoint'] = url_for('api.api_root', _external=True)
    return jsonify({"@context": context})


@api_blueprint.route('/d/<code>')
def decode(code):
    try:
        return redirect(decoded_url(code))
    except Exception:
        return Error('invalid URL').flask()


@ns_blueprint.route('/')  # noqa: F811
def index():
    context = Response._context.copy()
    context['endpoint'] = url_for('api.api_root', _external=True)
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
        'outformat': None,
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
            if current_app.debug or current_app.config['TESTING']:
                raise
            if not isinstance(ex, Error):
                msg = "{}".format(ex)
                ex = Error(message=msg, status=500)
            response = ex
            response.parameters = raw_params
            logger.exception(ex)

        if 'parameters' in response and not params['with_parameters']:
            del response.parameters

        logger.info('Response: {}'.format(response))
        mime = request.accept_mimetypes\
                      .best_match(MIMETYPES.keys(),
                                  DEFAULT_MIMETYPE)

        mimeformat = MIMETYPES.get(mime, DEFAULT_FORMAT)
        outformat = params['outformat'] or mimeformat

        return response.flask(
            in_headers=params['inHeaders'],
            headers=headers,
            prefix=params.get('prefix', encoded_url()),
            context_uri=url_for('api.context',
                                entity=type(response).__name__,
                                _external=True),
            outformat=outformat,
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
