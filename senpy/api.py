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

from future.utils import iteritems
from .models import Error, Results, Entry, from_string
import logging
logger = logging.getLogger(__name__)

boolean = [True, False]

processors = {
    'string_to_tuple': lambda p: p if isinstance(p, (tuple, list)) else tuple(p.split(','))
}

API_PARAMS = {
    "algorithm": {
        "aliases": ["algorithms", "a", "algo"],
        "required": True,
        "default": 'default',
        "processor": 'string_to_tuple',
        "description": ("Algorithms that will be used to process the request."
                        "It may be a list of comma-separated names."),
    },
    "expanded-jsonld": {
        "@id": "expanded-jsonld",
        "description": "use JSON-LD expansion to get full URIs",
        "aliases": ["expanded", "expanded_jsonld"],
        "options": boolean,
        "required": True,
        "default": False
    },
    "with-parameters": {
        "aliases": ['withparameters',
                    'with_parameters'],
        "description": "include initial parameters in the response",
        "options": boolean,
        "default": False,
        "required": True
    },
    "outformat": {
        "@id": "outformat",
        "aliases": ["o"],
        "default": "json-ld",
        "description": """The data can be semantically formatted (JSON-LD, turtle or n-triples),
given as a list of comma-separated fields (see the fields option) or constructed from a Jinja2
template (see the template option).""",
        "required": True,
        "options": ["json-ld", "turtle", "ntriples"],
    },
    "template": {
        "@id": "template",
        "required": False,
        "description": """Jinja2 template for the result. The input data for the template will
be the results as a dictionary.
For example:

Consider the results before templating:

```
[{
    "@type": "entry",
    "onyx:hasEmotionSet": [],
    "nif:isString": "testing the template",
    "marl:hasOpinion": [
        {
            "@type": "sentiment",
            "marl:hasPolarity": "marl:Positive"
        }
    ]
}]
```


And the template:

```
{% for entry in entries %}
{{ entry["nif:isString"] | upper }},{{entry.sentiments[0]["marl:hasPolarity"].split(":")[1]}}
{% endfor %}
```

The final result would be:

```
TESTING THE TEMPLATE,Positive
```
"""

    },
    "fields": {
        "@id": "fields",
        "required": False,
        "description": """A jmespath selector, that can be used to extract a new dictionary, array or value
from the results.
jmespath is a powerful query language for json and/or dictionaries.
It allows you to change the structure (and data) of your objects through queries.

e.g., the following expression gets a list of `[emotion label, intensity]` for each entry:
`entries[]."onyx:hasEmotionSet"[]."onyx:hasEmotion"[]["onyx:hasEmotionCategory","onyx:hasEmotionIntensity"]`

For more information, see: https://jmespath.org

"""
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
        "description": "Show all properties in the result",
        "aliases": ["v"],
        "required": True,
        "options": boolean,
        "default": False
    },
    "aliases": {
        "@id": "aliases",
        "description": "Replace JSON properties with their aliases",
        "aliases": [],
        "required": True,
        "options": boolean,
        "default": False
    },
    "emotion-model": {
        "@id": "emotionModel",
        "description": """Emotion model to use in the response.
Senpy will try to convert the output to this model automatically.

Examples: `wna:liking` and `emoml:big6`.
        """,
        "aliases": ["emoModel", "emotionModel"],
        "required": False
    },
    "conversion": {
        "@id": "conversion",
        "description": """How to show the elements that have (not) been converted.

* full: converted and original elements will appear side-by-side
* filtered: only converted elements will be shown
* nested: converted elements will be shown, and they will include a link to the original element
(using `prov:wasGeneratedBy`).
""",
        "required": True,
        "options": ["filtered", "nested", "full"],
        "default": "full"
    }
}

EVAL_PARAMS = {
    "algorithm": {
        "aliases": ["plug", "p", "plugins", "algorithms", 'algo', 'a', 'plugin'],
        "description": "Plugins to evaluate",
        "required": True,
        "help": "See activated plugins in /plugins",
        "processor": API_PARAMS['algorithm']['processor']
    },
    "dataset": {
        "aliases": ["datasets", "data", "d"],
        "description": "Datasets to be evaluated",
        "required": True,
        "help": "See avalaible datasets in /datasets"
    }
}

PLUGINS_PARAMS = {
    "plugin-type": {
        "@id": "pluginType",
        "description": 'What kind of plugins to list',
        "aliases": ["pluginType", "plugin_type"],
        "required": True,
        "default": 'analysisPlugin'
    }
}

WEB_PARAMS = {
    "in-headers": {
        "aliases": ["headers", "inheaders", "inHeaders", "in-headers", "in_headers"],
        "description": "Only include the JSON-LD context in the headers",
        "required": True,
        "default": False,
        "options": boolean
    },
}

CLI_PARAMS = {
    "plugin-folder": {
        "aliases": ["folder", "plugin_folder"],
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
        "description": "input type",
        "aliases": ["t"],
        "required": False,
        "default": "direct",
        "options": ["direct", "url", "file"],
    },
    "informat": {
        "@id": "informat",
        "description": "input format",
        "aliases": ["f"],
        "required": False,
        "default": "text",
        "options": ["text", "json-ld"],
    },
    "language": {
        "@id": "language",
        "description": "language of the input",
        "aliases": ["l"],
        "required": False,
    },
    "prefix": {
        "@id": "prefix",
        "description": "prefix to use for new entities",
        "aliases": ["p"],
        "required": True,
        "default": "",
    },
    "urischeme": {
        "@id": "urischeme",
        "description": "scheme for NIF URIs",
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
                    break
            if param not in outdict:
                if "default" in options:
                    # We assume the default is correct
                    outdict[param] = options["default"]
                elif options.get("required", False):
                    wrong_params[param] = spec[param]
                continue
            if 'processor' in options:
                outdict[param] = processors[options['processor']](outdict[param])
            if "options" in options:
                if options["options"] == boolean:
                    outdict[param] = str(outdict[param]).lower() in ['true', '1', '']
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


def parse_analyses(params, plugins):
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
        entry = Entry(nif__isString=params['input'], id='prefix:')  # Use @base
        results.entries.append(entry)
    elif params['informat'] == 'json-ld':
        results = from_string(params['input'], cls=Results)
    else:  # pragma: no cover
        raise NotImplementedError('Informat {} is not implemented'.format(
            params['informat']))
    results.parameters = params
    return results
