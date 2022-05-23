#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
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
#
"""
Blueprints for Senpy
"""
from flask import (Blueprint, request, current_app, render_template, url_for,
                   jsonify, redirect)
from .models import Error, Response, Help, Plugins, read_schema, dump_schema, Datasets
from . import api
from .version import __version__
from functools import wraps

from .gsitk_compat import GSITK_AVAILABLE, datasets

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


def encode_url(url=None):
    code = ''
    if not url:
        url = request.parameters.get('prefix', request.full_path[1:] + '#')
    return code or base64.urlsafe_b64encode(url.encode()).decode()


def url_for_code(code, base=None):
    # if base:
    #     return base + code
    # return url_for('api.decode', code=code, _external=True)
    # This was producing unique yet very long URIs, which wasn't ideal for visualization.
    return 'http://senpy.invalid/'


def decoded_url(code, base=None):
    path = base64.urlsafe_b64decode(code.encode()).decode()
    if path[:4] == 'http':
        return path
    base = base or request.url_root
    return base + path


@demo_blueprint.route('/')
def index():
    # ev = str(get_params(request).get('evaluation', True))
    # evaluation_enabled = ev.lower() not in ['false', 'no', 'none']
    evaluation_enabled = GSITK_AVAILABLE

    return render_template("index.html",
                           evaluation=evaluation_enabled,
                           version=__version__)


@api_blueprint.route('/contexts/<code>')
def context(code=''):
    context = Response._context
    context['@base'] = url_for('api.decode', code=code, _external=True)
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
        'in-headers': False,
        'expanded-jsonld': False,
        'outformat': None,
        'with-parameters': True,
    }

    @wraps(f)
    def decorated_function(*args, **kwargs):
        raw_params = get_params(request)
        # logger.info('Getting request: {}'.format(raw_params))
        logger.debug('Getting request. Params: {}'.format(raw_params))
        headers = {'X-ORIGINAL-PARAMS': json.dumps(raw_params)}
        params = default_params

        mime = request.accept_mimetypes\
                      .best_match(MIMETYPES.keys(),
                                  DEFAULT_MIMETYPE)

        mimeformat = MIMETYPES.get(mime, DEFAULT_FORMAT)
        outformat = mimeformat

        try:
            params = api.parse_params(raw_params, api.WEB_PARAMS, api.API_PARAMS)
            outformat = params.get('outformat', mimeformat)
            if hasattr(request, 'parameters'):
                request.parameters.update(params)
            else:
                request.parameters = params
            response = f(*args, **kwargs)

            if 'parameters' in response and not params['with-parameters']:
                del response.parameters

            logger.debug('Response: {}'.format(response))

            prefix = params.get('prefix')
            code = encode_url(prefix)

            return response.flask(
                in_headers=params['in-headers'],
                headers=headers,
                prefix=prefix or url_for_code(code),
                base=prefix,
                context_uri=url_for('api.context',
                                    code=code,
                                    _external=True),
                outformat=outformat,
                expanded=params['expanded-jsonld'],
                template=params.get('template'),
                verbose=params['verbose'],
                aliases=params['aliases'],
                fields=params.get('fields'))

        except (Exception) as ex:
            if current_app.debug or current_app.config['TESTING']:
                raise
            if not isinstance(ex, Error):
                msg = "{}".format(ex)
                ex = Error(message=msg, status=500)
            response = ex
            response.parameters = raw_params
            logger.exception(ex)
            return response.flask(
                outformat=outformat,
                expanded=params['expanded-jsonld'],
                verbose=params.get('verbose', True),
            )

    return decorated_function


@api_blueprint.route('/', defaults={'plugins': None}, methods=['POST', 'GET'], strict_slashes=False)
@api_blueprint.route('/<path:plugins>', methods=['POST', 'GET'], strict_slashes=False)
@basic_api
def api_root(plugins):
    if plugins:
        if request.parameters['algorithm'] != api.API_PARAMS['algorithm']['default']:
            raise Error('You cannot specify the algorithm with a parameter and a URL variable.'
                        ' Please, remove one of them')
        plugins = plugins.replace('+', ',').replace('/', ',')
        plugins = api.processors['string_to_tuple'](plugins)
    else:
        plugins = request.parameters['algorithm']

    print(plugins)

    sp = current_app.senpy
    plugins = sp.get_plugins(plugins)

    if request.parameters['help']:
        apis = [api.WEB_PARAMS, api.API_PARAMS, api.NIF_PARAMS]
        # Verbose is set to False as default, but we want it to default to
        # True for help. This checks the original value, to make sure it wasn't
        # set by default.
        if not request.parameters['verbose'] and get_params(request).get('verbose'):
            apis = []
        if request.parameters['algorithm'] == ['default', ]:
            plugins = []
        allparameters = api.get_all_params(plugins, *apis)
        response = Help(valid_parameters=allparameters)
        return response
    req = api.parse_call(request.parameters)
    analyses = api.parse_analyses(req.parameters, plugins)
    results = current_app.senpy.analyse(req, analyses)
    return results


@api_blueprint.route('/evaluate', methods=['POST', 'GET'], strict_slashes=False)
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


@api_blueprint.route('/plugins', methods=['POST', 'GET'], strict_slashes=False)
@basic_api
def plugins():
    sp = current_app.senpy
    params = api.parse_params(request.parameters, api.PLUGINS_PARAMS)
    ptype = params.get('plugin-type')
    plugins = list(sp.analysis_plugins(plugin_type=ptype))
    dic = Plugins(plugins=plugins)
    return dic


@api_blueprint.route('/plugins/<plugin>', methods=['POST', 'GET'], strict_slashes=False)
@basic_api
def plugin(plugin):
    sp = current_app.senpy
    return sp.get_plugin(plugin)


@api_blueprint.route('/datasets', methods=['POST', 'GET'], strict_slashes=False)
@basic_api
def get_datasets():
    dic = Datasets(datasets=list(datasets.values()))
    return dic
