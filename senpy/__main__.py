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
"""
Senpy is a modular sentiment analysis server. This script runs an instance of
the server.

"""

from flask import Flask
from senpy.extensions import Senpy
from gevent.wsgi import WSGIServer
from gevent.monkey import patch_all
import logging
import os
import sys
import argparse
import senpy

patch_all(thread=False)

SERVER_PORT = os.environ.get("PORT", 5000)


def info(type, value, tb):
    if hasattr(sys, 'ps1') or not sys.stderr.isatty():
        #  we are in interactive mode or we don't have a tty-like
        #  device, so we call the default hook
        sys.__excepthook__(type, value, tb)
    else:
        import traceback
        import pdb
        # we are NOT in interactive mode, print the exception...
        traceback.print_exception(type, value, tb)
        print
        # ...then start the debugger in post-mortem mode.
        # pdb.pm() # deprecated
        pdb.post_mortem(tb)  # more "modern"


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
        '--debug',
        '-d',
        action='store_true',
        default=False,
        help='Run the application in debug mode')
    parser.add_argument(
        '--default-plugins',
        action='store_true',
        default=False,
        help='Load the default plugins')
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
        default='plugins',
        help='Where to look for plugins.')
    parser.add_argument(
        '--only-install',
        '-i',
        action='store_true',
        default=False,
        help='Do not run a server, only install plugin dependencies')
    args = parser.parse_args()
    logging.basicConfig()
    rl = logging.getLogger()
    rl.setLevel(getattr(logging, args.level))
    app = Flask(__name__)
    app.debug = args.debug
    if args.debug:
        sys.excepthook = info
    sp = Senpy(app, args.plugins_folder, default_plugins=args.default_plugins)
    if args.only_install:
        sp.install_deps()
        return
    sp.activate_all()
    http_server = WSGIServer((args.host, args.port), app)
    try:
        print('Senpy version {}'.format(senpy.__version__))
        print('Server running on port %s:%d. Ctrl+C to quit' % (args.host,
                                                                args.port))
        http_server.serve_forever()
    except KeyboardInterrupt:
        print('Bye!')
    http_server.stop()
    sp.deactivate_all()


if __name__ == '__main__':
    main()
