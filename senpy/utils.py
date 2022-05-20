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
from . import models, __version__
from collections.abc import MutableMapping
import pprint
import pdb

import logging
logger = logging.getLogger(__name__)

# MutableMapping should be enough, but it causes problems with py2
DICTCLASSES = (MutableMapping, dict, models.BaseModel)


def check_template(indict, template):
    if isinstance(template, DICTCLASSES) and isinstance(indict, DICTCLASSES):
        for k, v in template.items():
            if k not in indict:
                raise models.Error('{} not in {}'.format(k, indict))
            check_template(indict[k], v)
    elif isinstance(template, list) and isinstance(indict, list):
        for e in template:
            for i in indict:
                try:
                    check_template(i, e)
                    break
                except models.Error as ex:
                    # raise
                    continue
            else:
                raise models.Error(('Element not found.'
                                   '\nExpected: {}\nIn: {}').format(pprint.pformat(e),
                                                                    pprint.pformat(indict)))
    else:
        if indict != template:
            raise models.Error(('Differences found.\n'
                                '\tExpected: {}\n'
                                '\tFound: {}').format(pprint.pformat(template),
                                                      pprint.pformat(indict)))


def convert_dictionary(original, mappings):
    result = {}
    for key, value in original.items():
        if key in mappings:
            key = mappings[key]
        result[key] = value
    return result


def easy_load(app=None, plugin_list=None, plugin_folder=None, **kwargs):
    '''
    Run a server with a specific plugin.
    '''

    from flask import Flask
    from .extensions import Senpy

    if not app:
        app = Flask(__name__)
    sp = Senpy(app, plugin_folder=plugin_folder, **kwargs)
    if not plugin_list:
        from . import plugins
        import __main__
        plugin_list = plugins.from_module(__main__)
    for plugin in plugin_list:
        sp.add_plugin(plugin)
    sp.install_deps()
    sp.activate_all()
    return sp, app


def easy_test(plugin_list=None, debug=True):
    logger.setLevel(logging.DEBUG)
    logging.getLogger().setLevel(logging.INFO)
    try:
        if not plugin_list:
            import __main__
            logger.info('Loading classes from {}'.format(__main__))
            from . import plugins
            plugin_list = plugins.from_module(__main__)
        plugin_list = list(plugin_list)
        for plug in plugin_list:
            plug.test()
            plug.log.info('My tests passed!')
        logger.info('All tests passed for {} plugins!'.format(len(plugin_list)))
    except Exception:
        if not debug:
            raise
        pdb.post_mortem()


def easy(host='0.0.0.0', port=5000, debug=False, **kwargs):
    '''
    Run a server with a specific plugin.
    '''
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger('senpy').setLevel(logging.INFO)
    sp, app = easy_load(**kwargs)
    easy_test(sp.plugins())
    app.debug = debug
    import time
    logger.info(time.time())
    logger.info('Senpy version {}'.format(__version__))
    logger.info('Server running on port %s:%d. Ctrl+C to quit' % (host,
                                                                  port))
    app.debug = debug
    app.run(host,
            port,
            debug=app.debug)
