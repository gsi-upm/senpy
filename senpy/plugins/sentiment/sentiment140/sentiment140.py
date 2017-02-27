import requests
import json

from senpy.plugins import SentimentPlugin
from senpy.models import Sentiment


class Sentiment140Plugin(SentimentPlugin):
    def analyse_entry(self, entry, params):
        lang = params.get("language", "auto")
        res = requests.post("http://www.sentiment140.com/api/bulkClassifyJson",
                            json.dumps({
                                "language": lang,
                                "data": [{
                                    "text": entry.text
                                }]
                            }))
        p = params.get("prefix", None)
        polarity_value = self.maxPolarityValue * int(
            res.json()["data"][0]["polarity"]) * 0.25
        polarity = "marl:Neutral"
        neutral_value = self.maxPolarityValue / 2.0
        if polarity_value > neutral_value:
            polarity = "marl:Positive"
        elif polarity_value < neutral_value:
            polarity = "marl:Negative"

        sentiment = Sentiment(
            prefix=p,
            marl__hasPolarity=polarity,
            marl__polarityValue=polarity_value)
        sentiment.prov__wasGeneratedBy = self.id
        entry.sentiments = []
        entry.sentiments.append(sentiment)
        entry.language = lang
        yield entry
