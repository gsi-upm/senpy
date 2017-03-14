from future.utils import iteritems
from .models import Error
import logging
logger = logging.getLogger(__name__)

API_PARAMS = {
    "algorithm": {
        "aliases": ["algorithm", "a", "algo"],
        "required": False,
    },
    "outformat": {
        "@id": "outformat",
        "aliases": ["outformat", "o"],
        "default": "json-ld",
        "required": True,
        "options": ["json-ld", "turtle"],
    },
    "expanded-jsonld": {
        "@id": "expanded-jsonld",
        "aliases": ["expanded", "expanded-jsonld"],
        "required": True,
        "default": 0
    },
    "emotionModel": {
        "@id": "emotionModel",
        "aliases": ["emotionModel", "emoModel"],
        "required": False
    },
    "plugin_type": {
        "@id": "pluginType",
        "description": 'What kind of plugins to list',
        "aliases": ["pluginType", "plugin_type"],
        "required": True,
        "default": "analysisPlugin"
    },
    "conversion": {
        "@id": "conversion",
        "description": "How to show the elements that have (not) been converted",
        "required": True,
        "options": ["filtered", "nested", "full"],
        "default": "full"
    }
}

WEB_PARAMS = {
    "inHeaders": {
        "aliases": ["inHeaders", "headers"],
        "required": True,
        "default": "0"
    },
}

CLI_PARAMS = {
    "plugin_folder": {
        "aliases": ["plugin_folder", "folder"],
        "required": True,
        "default": "."
    },
}

NIF_PARAMS = {
    "input": {
        "@id": "input",
        "aliases": ["i", "input"],
        "required": True,
        "help": "Input text"
    },
    "informat": {
        "@id": "informat",
        "aliases": ["f", "informat"],
        "required": False,
        "default": "text",
        "options": ["turtle", "text", "json-ld"],
    },
    "intype": {
        "@id": "intype",
        "aliases": ["intype", "t"],
        "required": False,
        "default": "direct",
        "options": ["direct", "url", "file"],
    },
    "language": {
        "@id": "language",
        "aliases": ["language", "l"],
        "required": False,
    },
    "prefix": {
        "@id": "prefix",
        "aliases": ["prefix", "p"],
        "required": True,
        "default": "",
    },
    "urischeme": {
        "@id": "urischeme",
        "aliases": ["urischeme", "u"],
        "required": False,
        "default": "RFC5147String",
        "options": "RFC5147String"
    },
}


def parse_params(indict, spec=NIF_PARAMS):
    logger.debug("Parsing: {}\n{}".format(indict, spec))
    outdict = indict.copy()
    wrong_params = {}
    for param, options in iteritems(spec):
        if param[0] != "@":  # Exclude json-ld properties
            for alias in options.get("aliases", []):
                if alias in indict:
                    outdict[param] = indict[alias]
            if param not in outdict:
                if options.get("required", False) and "default" not in options:
                    wrong_params[param] = spec[param]
                else:
                    if "default" in options:
                        outdict[param] = options["default"]
            else:
                if "options" in spec[param] and \
                   outdict[param] not in spec[param]["options"]:
                    wrong_params[param] = spec[param]
    if wrong_params:
        logger.debug("Error parsing: %s", wrong_params)
        message = Error(
            status=400,
            message="Missing or invalid parameters",
            parameters=outdict,
            errors={param: error
                    for param, error in iteritems(wrong_params)})
        raise message
    return outdict
