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
from __future__ import print_function

import sys
from .models import Error
from .extensions import Senpy
from . import api


def argv_to_dict(argv):
    '''Turns parameters in the form of '--key value' into a dict {'key': 'value'}
    '''
    cli_dict = {}

    for i in range(len(argv)):
        if argv[i][0] == '-':
            key = argv[i].strip('-')
            value = argv[i + 1] if len(argv) > i + 1 else None
            if not value or value[0] == '-':
                cli_dict[key] = True
            else:
                cli_dict[key] = value
    return cli_dict


def main_function(argv):
    '''This is the method for unit testing
    '''
    params = api.parse_params(argv_to_dict(argv),
                              api.CLI_PARAMS,
                              api.API_PARAMS,
                              api.NIF_PARAMS)
    plugin_folder = params['plugin-folder']
    default_plugins = not params.get('no-default-plugins', False)
    sp = Senpy(default_plugins=default_plugins, plugin_folder=plugin_folder)
    request = api.parse_call(params)
    algos = sp.get_plugins(request.parameters.get('algorithm', None))
    if algos:
        for algo in algos:
            sp.activate_plugin(algo.name)
    else:
        sp.activate_all()
    res = sp.analyse(request)
    return res


def main():
    '''This method is the entrypoint for the CLI (as configured un setup.py)
    '''
    try:
        res = main_function(sys.argv[1:])
        print(res.serialize())
    except Error as err:
        print(err.serialize(), file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
