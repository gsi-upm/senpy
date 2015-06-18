import json
import random

from senpy.plugins import SentimentPlugin
from senpy.models import Response, Opinion, Entry


class Sentiment140Plugin(SentimentPlugin):
    def analyse(self, **params):
        lang = params.get("language", "auto")

        p = params.get("prefix", None)
        response = Response(prefix=p)
        polarity_value = max(-1, min(1, random.gauss(0.2, 0.2)))
        polarity = "marl:Neutral"
        if polarity_value > 0:
            polarity = "marl:Positive"
        elif polarity_value < 0:
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
