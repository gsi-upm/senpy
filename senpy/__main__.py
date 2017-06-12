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

import logging
import os
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
    parser.add_argument(
        '--threaded',
        action='store_false',
        default=True,
        help='Run a threaded server')
    parser.add_argument(
        '--version',
        '-v',
        action='store_true',
        default=False,
        help='Output the senpy version and exit')
    args = parser.parse_args()
    if args.version:
        print('Senpy version {}'.format(senpy.__version__))
        exit(1)
    logging.basicConfig()
    rl = logging.getLogger()
    rl.setLevel(getattr(logging, args.level))
    app = Flask(__name__)
    app.debug = args.debug
    sp = Senpy(app, args.plugins_folder, default_plugins=args.default_plugins)
    if args.only_install:
        sp.install_deps()
        return
    sp.activate_all()
    print('Senpy version {}'.format(senpy.__version__))
    print('Server running on port %s:%d. Ctrl+C to quit' % (args.host,
                                                            args.port))
    app.run(args.host,
            args.port,
            threaded=args.threaded,
            debug=app.debug)
    sp.deactivate_all()


if __name__ == '__main__':
    main()
