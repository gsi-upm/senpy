import requests
import json

from senpy.plugins import SentimentPlugin
from senpy.models import Response, Opinion, Entry


class Sentiment140Plugin(SentimentPlugin):
    def analyse(self, **params):
        lang = params.get("language", "auto")
        res = requests.post("http://www.sentiment140.com/api/bulkClassifyJson",
                            json.dumps({"language": lang,
                                        "data": [{"text": params["input"]}]
                                        }
                                       )
                            )

        p = params.get("prefix", None)
        response = Response(prefix=p)
        polarity_value = self.maxPolarityValue*int(res.json()["data"][0]
                                                   ["polarity"]) * 0.25
        polarity = "marl:Neutral"
        if polarity_value > 50:
            polarity = "marl:Positive"
        elif polarity_value < 50:
            polarity = "marl:Negative"
        entry = Entry(id="Entry0",
                      text=params["input"],
                      prefix=p)
        opinion = Opinion(id="Opinion0",
                          prefix=p,
                          hasPolarity=polarity,
                          polarityValue=polarity_value)
        opinion["prov:wasGeneratedBy"] = self.id
        entry.opinions.append(opinion)
        entry.language = lang
        response.entries.append(entry)
        return response
