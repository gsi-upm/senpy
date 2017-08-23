import random

from senpy.plugins import SentimentPlugin
from senpy.models import Sentiment, Entry


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

    def test(self):
        params = dict()
        results = list()
        for i in range(100):
            res = next(self.analyse_entry(Entry(nif__isString="Hello"), params))
            res.validate()
            results.append(res.sentiments[0]['marl:hasPolarity'])
        assert 'marl:Positive' in results
        assert 'marl:Negative' in results
