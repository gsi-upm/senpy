import requests
import json

import sys

print(sys.path)
from senpy.plugin import SentimentPlugin

class Sentiment140Plugin(SentimentPlugin):
    def __init__(self, **kwargs):
        super(Sentiment140Plugin, self).__init__(name="Sentiment140",
                                                 version="1.0",
                                                 **kwargs)

    def analyse(self, **params):
        res = requests.post("http://www.sentiment140.com/api/bulkClassifyJson",
                            json.dumps({
                                "language": "auto",
                                "data": [{"text": params["input"]}]}
                                    ))


        response = {"analysis": [{}], "entries": []}
        response["analysis"][0].update({ "marl:algorithm": "SimpleAlgorithm",
                                        "marl:minPolarityValue": 0,
                                        "marl:maxPolarityValue": 100})
        polarityValue = int(res.json()["data"][0]["polarity"]) * 25
        polarity = "marl:Neutral"
        if polarityValue > 50:
            polarity = "marl:Positive"
        elif polarityValue < 50:
            polarity = "marl:Negative"

        response["entries"] = [
            {
                "isString": params["input"],
                "opinions": [{
                    "marl:polarityValue": polarityValue,
                    "marl:hasPolarity": polarity

                }]
            }
        ]

        return response


plugin = Sentiment140Plugin()
