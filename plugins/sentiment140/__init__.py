import requests
import json

from senpy.plugins import SentimentPlugin
from senpy.models import Response, Opinion, Entry


class Sentiment140Plugin(SentimentPlugin):
    EXTRA_PARAMS = {
        "language": {"aliases": ["language", "l"],
                     "required": False,
                     "options": ["es", "en", "auto"],
                     }
    }

    def __init__(self, **kwargs):
        super(Sentiment140Plugin, self).__init__(name="sentiment140",
                                                 version="2.0",
                                                 extraparams=self.EXTRA_PARAMS,
                                                 **kwargs)

    def analyse(self, **params):
        lang = params.get("language", "auto")
        res = requests.post("http://www.sentiment140.com/api/bulkClassifyJson",
                            json.dumps({"language": lang,
                                        "data": [{"text": params["input"]}]
                                        }
                                       )
                            )

        response = Response()
        polarity_value = int(res.json()["data"][0]["polarity"]) * 25
        polarity = "marl:Neutral"
        if polarity_value > 50:
            polarity = "marl:Positive"
        elif polarity_value < 50:
            polarity = "marl:Negative"
        entry = Entry(text=params["input"],
                      prefix=params.get("prefix", ""))
        opinion = Opinion(hasPolarity=polarity,
                          polarityValue=polarity_value,
                          prefix=params.get("prefix", ""))
        opinion["prov:wasGeneratedBy"] = self.id
        entry.opinions.append(opinion)
        entry.language = lang
        response.entries.append(entry)
        return response

plugin = Sentiment140Plugin()
