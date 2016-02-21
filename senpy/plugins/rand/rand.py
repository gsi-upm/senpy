import json
import random

from senpy.plugins import SentimentPlugin
from senpy.models import Results, Sentiment, Entry


class Sentiment140Plugin(SentimentPlugin):
    def analyse(self, **params):
        lang = params.get("language", "auto")

        response = Results()
        polarity_value = max(-1, min(1, random.gauss(0.2, 0.2)))
        polarity = "marl:Neutral"
        if polarity_value > 0:
            polarity = "marl:Positive"
        elif polarity_value < 0:
            polarity = "marl:Negative"
        entry = Entry({"id":":Entry0",
                       "nif:isString": params["input"]})
        sentiment = Sentiment({"id": ":Sentiment0",
                               "marl:hasPolarity": polarity,
                               "marl:polarityValue": polarity_value})
        sentiment["prov:wasGeneratedBy"] = self.id
        entry.sentiments = []
        entry.sentiments.append(sentiment)
        entry.language = lang
        response.entries.append(entry)
        return response












