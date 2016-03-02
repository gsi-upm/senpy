from future.utils import iteritems
import logging
logger = logging.getLogger(__name__)

from .models import Error

API_PARAMS = {
    "algorithm": {
        "aliases": ["algorithm", "a", "algo"],
        "required": False,
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
        "options": ["turtle", "text"],
    },
    "intype": {
        "@id": "intype",
        "aliases": ["intype", "t"],
        "required": False,
        "default": "direct",
        "options": ["direct", "url", "file"],
    },
    "outformat": {
        "@id": "outformat",
        "aliases": ["outformat", "o"],
        "default": "json-ld",
        "required": False,
        "options": ["json-ld"],
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
    outdict = {}
    wrong_params = {}
    for param, options in iteritems(spec):
        if param[0] != "@":  # Exclude json-ld properties
            logger.debug("Param: %s - Options: %s", param, options)
            for alias in options["aliases"]:
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
        message = Error(status=404,
                        message="Missing or invalid parameters",
                        parameters=outdict,
                        errors={param: error for param, error in
                                iteritems(wrong_params)})
        raise message
    return outdict
