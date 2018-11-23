from future.utils import iteritems
from .models import Analysis, Error, Results, Entry, from_string
import logging
logger = logging.getLogger(__name__)

boolean = [True, False]

API_PARAMS = {
    "algorithm": {
        "aliases": ["algorithms", "a", "algo"],
        "required": True,
        "default": 'default',
        "description": ("Algorithms that will be used to process the request."
                        "It may be a list of comma-separated names."),
    },
    "expanded-jsonld": {
        "@id": "expanded-jsonld",
        "aliases": ["expanded"],
        "options": boolean,
        "required": True,
        "default": False
    },
    "with_parameters": {
        "aliases": ['withparameters',
                    'with-parameters'],
        "options": boolean,
        "default": False,
        "required": True
    },
    "outformat": {
        "@id": "outformat",
        "aliases": ["o"],
        "default": "json-ld",
        "required": True,
        "options": ["json-ld", "turtle", "ntriples"],
    },
    "help": {
        "@id": "help",
        "description": "Show additional help to know more about the possible parameters",
        "aliases": ["h"],
        "required": True,
        "options": boolean,
        "default": False
    },
    "verbose": {
        "@id": "verbose",
        "description": "Show all help, including the common API parameters, or only plugin-related info",
        "aliases": ["v"],
        "required": True,
        "options": boolean,
        "default": True
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
        "options": boolean
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
        "options": ["RFC5147String", ]
    }
}

BUILTIN_PARAMS = {}

for d in [
        NIF_PARAMS, CLI_PARAMS, WEB_PARAMS, PLUGINS_PARAMS, EVAL_PARAMS,
        API_PARAMS
]:
    for k, v in d.items():
        BUILTIN_PARAMS[k] = v


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
            elif "options" in options:
                if options["options"] == boolean:
                    outdict[param] = str(outdict[param]).lower() in ['true', '1']
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
    return outdict


def get_all_params(plugins, *specs):
    '''Return a list of parameters for a given set of specifications and plugins.'''
    dic = {}
    for s in specs:
        dic.update(s)
    dic.update(get_extra_params(plugins))
    return dic


def get_extra_params(plugins):
    '''Get a list of possible parameters given a list of plugins'''
    params = {}
    extra_params = {}
    for plugin in plugins:
        this_params = plugin.get('extra_params', {})
        for k, v in this_params.items():
            if k not in extra_params:
                extra_params[k] = {}
            extra_params[k][plugin.name] = v
    for k, v in extra_params.items():  # Resolve conflicts
        if len(v) == 1:  # Add the extra options that do not collide
            params[k] = list(v.values())[0]
        else:
            required = False
            aliases = None
            options = None
            default = None
            nodefault = False  # Set when defaults are not compatible

            for plugin, opt in v.items():
                params['{}.{}'.format(plugin, k)] = opt
                required = required or opt.get('required', False)
                newaliases = set(opt.get('aliases', []))
                if aliases is None:
                    aliases = newaliases
                else:
                    aliases = aliases & newaliases
                if 'options' in opt:
                    newoptions = set(opt['options'])
                    options = newoptions if options is None else options & newoptions
                if 'default' in opt:
                    newdefault = opt['default']
                    if newdefault:
                        if default is None and not nodefault:
                            default = newdefault
                        elif newdefault != default:
                            nodefault = True
                            default = None
            # Check for incompatibilities
            if options != set():
                params[k] = {
                    'default': default,
                    'aliases': list(aliases),
                    'required': required,
                    'options': list(options)
                }
    return params


def parse_analysis(params, plugins):
    '''
    Parse the given parameters individually for each plugin, and get a list of the parameters that
    belong to each of the plugins. Each item can then be used in the plugin.analyse_entries method.
    '''
    analysis_list = []
    for i, plugin in enumerate(plugins):
        if not plugin:
            continue
        this_params = filter_params(params, plugin, i)
        parsed = parse_params(this_params, plugin.get('extra_params', {}))
        analysis = plugin.activity(parsed)
        analysis_list.append(analysis)
    return analysis_list


def filter_params(params, plugin, ith=-1):
    '''
    Get the values within params that apply to a plugin.
    More specific names override more general names, in this order:

    <index_order>.parameter > <plugin.name>.parameter > parameter


    Example:

    >>> filter_params({'0.hello': True, 'hello': False}, Plugin(), 0)
    { '0.hello': True, 'hello': True}

    '''
    thisparams = {}
    if ith >= 0:
        ith = '{}.'.format(ith)
    else:
        ith = ""
    for k, v in params.items():
        if ith and k.startswith(str(ith)):
            thisparams[k[len(ith):]] = v
        elif k.startswith(plugin.name):
            thisparams[k[len(plugin.name) + 1:]] = v
        elif k not in thisparams:
            thisparams[k] = v
    return thisparams


def parse_call(params):
    '''
    Return a results object based on the parameters used in a call/request.
    '''
    params = parse_params(params, NIF_PARAMS)
    if params['informat'] == 'text':
        results = Results()
        entry = Entry(nif__isString=params['input'], id='#')  # Use @base
        results.entries.append(entry)
    elif params['informat'] == 'json-ld':
        results = from_string(params['input'], cls=Results)
    else:  # pragma: no cover
        raise NotImplementedError('Informat {} is not implemented'.format(
            params['informat']))
    results.parameters = params
    return results
