#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""
Senpy is a modular sentiment analysis server. This script runs an instance of
the server.

"""

from flask import Flask
from senpy.extensions import Senpy
from senpy.utils import easy_test

import logging
import os
import sys
import argparse
import senpy

SERVER_PORT = os.environ.get("PORT", 5000)


def main():
    parser = argparse.ArgumentParser(description='Run a Senpy server')
    parser.add_argument(
        '--level',
        '-l',
        metavar='logging_level',
        type=str,
        default="INFO",
        help='Logging level')
    parser.add_argument(
        '--no-proxy-fix',
        action='store_true',
        default=False,
        help='Do not assume senpy will be running behind a proxy (e.g., nginx)')
    parser.add_argument(
        '--log-format',
        metavar='log_format',
        type=str,
        default='%(asctime)s %(levelname)-10s %(name)-30s \t %(message)s',
        help='Logging format')
    parser.add_argument(
        '--debug',
        '-d',
        action='store_true',
        default=False,
        help='Run the application in debug mode')
    parser.add_argument(
        '--no-default-plugins',
        action='store_true',
        default=False,
        help='Do not load the default plugins')
    parser.add_argument(
        '--host',
        type=str,
        default="0.0.0.0",
        help='Use 0.0.0.0 to accept requests from any host.')
    parser.add_argument(
        '--port',
        '-p',
        type=int,
        default=SERVER_PORT,
        help='Port to listen on.')
    parser.add_argument(
        '--plugins-folder',
        '-f',
        type=str,
        action='append',
        help='Where to look for plugins.')
    parser.add_argument(
        '--only-install',
        '-i',
        action='store_true',
        default=False,
        help='Do not run a server, only install plugin dependencies')
    parser.add_argument(
        '--only-test',
        action='store_true',
        default=False,
        help='Do not run a server, just test all plugins')
    parser.add_argument(
        '--test',
        '-t',
        action='store_true',
        default=False,
        help='Test all plugins before launching the server')
    parser.add_argument(
        '--only-list',
        '--list',
        action='store_true',
        default=False,
        help='Do not run a server, only list plugins found')
    parser.add_argument(
        '--data-folder',
        '--data',
        type=str,
        default=None,
        help='Where to look for data. It be set with the SENPY_DATA environment variable as well.')
    parser.add_argument(
        '--no-threaded',
        action='store_true',
        default=False,
        help='Run a single-threaded server')
    parser.add_argument(
        '--no-deps',
        '-n',
        action='store_true',
        default=False,
        help='Skip installing dependencies')
    parser.add_argument(
        '--version',
        '-v',
        action='store_true',
        default=False,
        help='Output the senpy version and exit')
    parser.add_argument(
        '--allow-fail',
        '--fail',
        action='store_true',
        default=False,
        help='Do not exit if some plugins fail to activate')
    parser.add_argument(
        '--enable-cors',
        '--cors',
        action='store_true',
        default=False,
        help='Enable CORS for all domains (requires flask-cors to be installed)')
    args = parser.parse_args()
    print('Senpy version {}'.format(senpy.__version__))
    print(sys.version)
    if args.version:
        exit(1)
    rl = logging.getLogger()
    rl.setLevel(getattr(logging, args.level))
    logger_handler = rl.handlers[0]

    # First, generic formatter:
    logger_handler.setFormatter(logging.Formatter(args.log_format))

    app = Flask(__name__)
    app.debug = args.debug

    sp = Senpy(app,
               plugin_folder=None,
               default_plugins=not args.no_default_plugins,
               data_folder=args.data_folder)
    folders = list(args.plugins_folder) if args.plugins_folder else []
    if not folders:
        folders.append(".")
    for p in folders:
        sp.add_folder(p)

    plugins = sp.plugins(plugin_type=None, is_activated=False)
    maxname = max(len(x.name) for x in plugins)
    maxversion = max(len(str(x.version)) for x in plugins)
    print('Found {} plugins:'.format(len(plugins)))
    for plugin in plugins:
        import inspect
        fpath = inspect.getfile(plugin.__class__)
        print('\t{: <{maxname}} @ {: <{maxversion}} -> {}'.format(plugin.name,
                                                                  plugin.version,
                                                                  fpath,
                                                                  maxname=maxname,
                                                                  maxversion=maxversion))
    if args.only_list:
        return
    if not args.no_deps:
        sp.install_deps()
    if args.only_install:
        return
    sp.activate_all(allow_fail=args.allow_fail)
    if args.test or args.only_test:
        easy_test(sp.plugins(), debug=args.debug)
        if args.only_test:
            return
    print('Senpy version {}'.format(senpy.__version__))
    print('Server running on port %s:%d. Ctrl+C to quit' % (args.host,
                                                            args.port))
    if args.enable_cors:
        from flask_cors import CORS
        CORS(app)

    if not args.no_proxy_fix:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    try:
        app.run(args.host,
                args.port,
                threaded=not args.no_threaded,
                debug=app.debug)
    except KeyboardInterrupt:
        print('Bye!')
    sp.deactivate_all()


if __name__ == '__main__':
    main()
