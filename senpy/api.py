from future.utils import iteritems
from .models import Error, Results, Entry, from_string
import logging
logger = logging.getLogger(__name__)

API_PARAMS = {
    "algorithm": {
        "aliases": ["algorithms", "a", "algo"],
        "required": False,
        "description": ("Algorithms that will be used to process the request."
                        "It may be a list of comma-separated names."),
    },
    "expanded-jsonld": {
        "@id": "expanded-jsonld",
        "aliases": ["expanded"],
        "options": "boolean",
        "required": True,
        "default": False
    },
    "with_parameters": {
        "aliases": ['withparameters',
                    'with-parameters'],
        "options": "boolean",
        "default": False,
        "required": True
    },
    "outformat": {
        "@id": "outformat",
        "aliases": ["o"],
        "default": "json-ld",
        "required": True,
        "options": ["json-ld", "turtle"],
    },
    "help": {
        "@id": "help",
        "description": "Show additional help to know more about the possible parameters",
        "aliases": ["h"],
        "required": True,
        "options": "boolean",
        "default": False
    },
    "emotionModel": {
        "@id": "emotionModel",
        "aliases": ["emoModel"],
        "required": False
    },
    "conversion": {
        "@id": "conversion",
        "description": "How to show the elements that have (not) been converted",
        "required": True,
        "options": ["filtered", "nested", "full"],
        "default": "full"
    }
}

EVAL_PARAMS = {
    "algorithm": {
        "aliases": ["plug", "p", "plugins", "algorithms", 'algo', 'a', 'plugin'],
        "description": "Plugins to be evaluated",
        "required": True,
        "help": "See activated plugins in /plugins"
    },
    "dataset": {
        "aliases": ["datasets", "data", "d"],
        "description": "Datasets to be evaluated",
        "required": True,
        "help": "See avalaible datasets in /datasets"
    }
}

PLUGINS_PARAMS = {
    "plugin_type": {
        "@id": "pluginType",
        "description": 'What kind of plugins to list',
        "aliases": ["pluginType"],
        "required": True,
        "default": 'analysisPlugin'
    }
}

WEB_PARAMS = {
    "inHeaders": {
        "aliases": ["headers"],
        "required": True,
        "default": False,
        "options": "boolean"
    },
}

CLI_PARAMS = {
    "plugin_folder": {
        "aliases": ["folder"],
        "required": True,
        "default": "."
    },
}

NIF_PARAMS = {
    "input": {
        "@id": "input",
        "aliases": ["i"],
        "required": True,
        "help": "Input text"
    },
    "intype": {
        "@id": "intype",
        "aliases": ["t"],
        "required": False,
        "default": "direct",
        "options": ["direct", "url", "file"],
    },
    "informat": {
        "@id": "informat",
        "aliases": ["f"],
        "required": False,
        "default": "text",
        "options": ["text", "json-ld"],
    },
    "language": {
        "@id": "language",
        "aliases": ["l"],
        "required": False,
    },
    "prefix": {
        "@id": "prefix",
        "aliases": ["p"],
        "required": True,
        "default": "",
    },
    "urischeme": {
        "@id": "urischeme",
        "aliases": ["u"],
        "required": False,
        "default": "RFC5147String",
        "options": "RFC5147String"
    }
}


def parse_params(indict, *specs):
    if not specs:
        specs = [NIF_PARAMS]
    logger.debug("Parsing: {}\n{}".format(indict, specs))
    outdict = indict.copy()
    wrong_params = {}
    for spec in specs:
        for param, options in iteritems(spec):
            for alias in options.get("aliases", []):
                # Replace each alias with the correct name of the parameter
                if alias in indict and alias != param:
                    outdict[param] = indict[alias]
                    del outdict[alias]
                    continue
            if param not in outdict:
                if "default" in options:
                    # We assume the default is correct
                    outdict[param] = options["default"]
                elif options.get("required", False):
                    wrong_params[param] = spec[param]
                continue
            if "options" in options:
                if options["options"] == "boolean":
                    outdict[param] = outdict[param] in [None, True, 'true', '1']
                elif outdict[param] not in options["options"]:
                    wrong_params[param] = spec[param]
    if wrong_params:
        logger.debug("Error parsing: %s", wrong_params)
        message = Error(
            status=400,
            message='Missing or invalid parameters',
            parameters=outdict,
            errors=wrong_params)
        raise message
    if 'algorithm' in outdict and not isinstance(outdict['algorithm'], list):
        outdict['algorithm'] = outdict['algorithm'].split(',')
    return outdict


def parse_extra_params(request, plugin=None):
    params = request.parameters.copy()
    if plugin:
        extra_params = parse_params(params, plugin.get('extra_params', {}))
        params.update(extra_params)
    return params


def parse_call(params):
    '''Return a results object based on the parameters used in a call/request.
    '''
    params = parse_params(params, NIF_PARAMS)
    if params['informat'] == 'text':
        results = Results()
        entry = Entry(nif__isString=params['input'])
        results.entries.append(entry)
    elif params['informat'] == 'json-ld':
        results = from_string(params['input'], cls=Results)
    else:  # pragma: no cover
        raise NotImplementedError('Informat {} is not implemented'.format(params['informat']))
    results.parameters = params
    return results
