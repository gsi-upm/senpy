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
This is a helper for development. If you want to run Senpy use:

    python -m senpy
"""
from gevent.monkey import patch_all; patch_all()
import gevent
import config
from flask import Flask
from senpy.extensions import Senpy
import logging
import os
from gevent.wsgi import WSGIServer

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
mypath = os.path.dirname(os.path.realpath(__file__))
sp = Senpy(app, os.path.join(mypath, "plugins"), default_plugins=True)
sp.activate_all()

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=config.DEBUG)
    app.debug = config.DEBUG
    http_server = WSGIServer(('', config.SERVER_PORT), app)
    http_server.serve_forever()
