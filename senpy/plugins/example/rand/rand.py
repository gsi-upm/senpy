import random

from senpy.plugins import SentimentPlugin
from senpy.models import Sentiment


class RandPlugin(SentimentPlugin):
    def analyse_entry(self, entry, params):
        lang = params.get("language", "auto")

        polarity_value = max(-1, min(1, random.gauss(0.2, 0.2)))
        polarity = "marl:Neutral"
        if polarity_value > 0:
            polarity = "marl:Positive"
        elif polarity_value < 0:
            polarity = "marl:Negative"
        sentiment = Sentiment({
            "marl:hasPolarity": polarity,
            "marl:polarityValue": polarity_value
        })
        sentiment["prov:wasGeneratedBy"] = self.id
        entry.sentiments.append(sentiment)
        entry.language = lang
        yield entry
