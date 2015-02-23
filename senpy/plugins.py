import logging
import ConfigParser
from .models import Leaf

logger = logging.getLogger(__name__)

PARAMS = {"input": {"aliases": ["i", "input"],
                    "required": True,
                    "help": "Input text"
                    },
          "informat": {"aliases": ["f", "informat"],
                       "required": False,
                       "default": "text",
                       "options": ["turtle", "text"],
                       },
          "intype": {"aliases": ["intype", "t"],
                     "required": False,
                     "default": "direct",
                     "options": ["direct", "url", "file"],
                     },
          "outformat": {"aliases": ["outformat", "o"],
                        "default": "json-ld",
                        "required": False,
                        "options": ["json-ld"],
                        },
          "language": {"aliases": ["language", "l"],
                       "required": False,
                       "options": ["es", "en"],
                       },
          "prefix": {"aliases": ["prefix", "p"],
                     "required": True,
                     "default": "",
          },
          "urischeme": {"aliases": ["urischeme", "u"],
                        "required": False,
                        "default": "RFC5147String",
                        "options": "RFC5147String"
                        },
          }


class SenpyPlugin(Leaf):
    _context = {"@vocab": "http://www.gsi.dit.upm.es/ontologies/senpy/ns#",
                "info": None}
    _frame = { "@context": _context,
              "name": {},
              "@explicit": False,
              "version": {},
              "repo": None,
              "info": None,
              }
    def __init__(self, info=None):
        if not info:
            raise ValueError("You need to provide configuration information for the plugin.")
        logger.debug("Initialising {}".format(info))
        super(SenpyPlugin, self).__init__()
        self.name = info["name"]
        self.version = info["version"]
        self.id="{}_{}".format(self.name, self.version)
        self.params = info.get("params", PARAMS.copy())
        self.extra_params = info.get("extra_params", {})
        self.params.update(self.extra_params)
        self.is_activated = False
        self.info = info

    def analyse(self, *args, **kwargs):
        logger.debug("Analysing with: {} {}".format(self.name, self.version))
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass


    @property
    def id(self):
        return "{}_{}".format(self.name, self.version)


class SentimentPlugin(SenpyPlugin):
    def __init__(self, info, *args, **kwargs):
        super(SentimentPlugin, self).__init__(info, *args, **kwargs)
        self.minPolarityValue = float(info.get("minPolarityValue", 0))
        self.maxPolarityValue = float(info.get("maxPolarityValue", 1))

class EmotionPlugin(SenpyPlugin):
    def __init__(self, info, *args, **kwargs):
        resp = super(EmotionPlugin, self).__init__(info, *args, **kwargs)
        self.minEmotionValue = float(info.get("minEmotionValue", 0))
        self.maxEmotionValue = float(info.get("maxEmotionValue", 0))
