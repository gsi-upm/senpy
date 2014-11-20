import logging

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
          "urischeme": {"aliases": ["urischeme", "u"],
                        "required": False,
                        "default": "RFC5147String",
                        "options": "RFC5147String"
                        },
          }


class SenpyPlugin(object):
    def __init__(self, name=None, version=None, extraparams=None, params=None):
        logger.debug("Initialising {}".format(name))
        self.name = name
        self.version = version
        if params:
            self.params = params
        else:
            self.params = PARAMS.copy()
            if extraparams:
                self.params.update(extraparams)
        self.extraparams = extraparams or {}
        self.enabled = True

    def analyse(self, *args, **kwargs):
        pass

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def jsonable(self, parameters=False):
        resp = {
            "@id": "{}_{}".format(self.name, self.version),
            "enabled": self.enabled,
        }
        if hasattr(self, "repo") and self.repo:
            resp["repo"] = self.repo.remotes[0].url
        if parameters:
            resp["parameters"] = self.params
        elif self.extraparams:
            resp["extra_parameters"] = self.extraparams
        return resp


class SentimentPlugin(SenpyPlugin):
    def __init__(self,
                 min_polarity_value=0,
                 max_polarity_value=1,
                 **kwargs):
        super(SentimentPlugin, self).__init__(**kwargs)
        self.minPolarityValue = min_polarity_value
        self.maxPolarityValue = max_polarity_value

    def jsonable(self, *args, **kwargs):
        resp = super(SentimentPlugin, self).jsonable(*args, **kwargs)
        resp["marl:maxPolarityValue"] = self.maxPolarityValue
        resp["marl:minPolarityValue"] = self.minPolarityValue
        return resp


class EmotionPlugin(SenpyPlugin):
    def __init__(self,
                 min_emotion_value=0,
                 max_emotion_value=1,
                 emotion_category=None,
                 **kwargs):
        super(EmotionPlugin, self).__init__(**kwargs)
        self.minEmotionValue = min_emotion_value
        self.maxEmotionValue = max_emotion_value
        self.emotionCategory = emotion_category

    def jsonable(self, *args, **kwargs):
        resp = super(EmotionPlugin, self).jsonable(*args, **kwargs)
        resp["onyx:minEmotionValue"] = self.minEmotionValue
        resp["onyx:maxEmotionValue"] = self.maxEmotionValue
        return resp
