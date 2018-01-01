from . import models
from collections import MutableMapping

# MutableMapping should be enough, but it causes problems with py2
DICTCLASSES = (MutableMapping, dict, models.BaseModel)


def check_template(indict, template):
    if isinstance(template, DICTCLASSES) and isinstance(indict, DICTCLASSES):
        for k, v in template.items():
            if k not in indict:
                return '{} not in {}'.format(k, indict)
            check_template(indict[k], v)
    elif isinstance(template, list) and isinstance(indict, list):
        for e in template:
            found = False
            for i in indict:
                try:
                    check_template(i, e)
                    found = True
                except models.Error as ex:
                    # raise
                    continue
            if not found:
                raise models.Error('{} not found in {}'.format(e, indict))
    else:
        if indict != template:
            raise models.Error('{} and {} are different'.format(indict, template))


def easy(app=None, plugin=None, host='0.0.0.0', port=5000, **kwargs):
    '''
    Run a server with a specific plugin.
    '''

    from flask import Flask
    from senpy.extensions import Senpy

    if not app:
        app = Flask(__name__)
    sp = Senpy(app)
    if plugin:
        sp.add_plugin(plugin)
    sp.install_deps()
    app.run(host,
            port,
            debug=app.debug,
            **kwargs)
