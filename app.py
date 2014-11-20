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
Simple Sentiment Analysis server for EUROSENTIMENT

This class shows how to use the nif_server module to create custom services.
"""
import config
from flask import Flask
from senpy.extensions import Senpy

app = Flask(__name__)

sp = Senpy()
sp.init_app(app)

if __name__ == '__main__':
    app.debug = config.DEBUG
    app.run(host="0.0.0.0", use_reloader=False)
