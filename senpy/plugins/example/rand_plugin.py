import random
from senpy import SentimentPlugin, Sentiment, Entry


class Rand(SentimentPlugin):
    '''A sample plugin that returns a random sentiment annotation'''
    author = "@balkian"
    version = '0.1'
    url = "https://github.com/gsi-upm/senpy-plugins-community"
    marl__maxPolarityValue = '1'
    marl__minPolarityValue = "-1"

    def analyse_entry(self, entry, params):
        polarity_value = max(-1, min(1, random.gauss(0.2, 0.2)))
        polarity = "marl:Neutral"
        if polarity_value > 0:
            polarity = "marl:Positive"
        elif polarity_value < 0:
            polarity = "marl:Negative"
        sentiment = Sentiment(marl__hasPolarity=polarity,
                              marl__polarityValue=polarity_value)
        sentiment.prov(self)
        entry.sentiments.append(sentiment)
        yield entry

    def test(self):
        '''Run several random analyses.'''
        params = dict()
        results = list()
        for i in range(50):
            res = next(self.analyse_entry(Entry(nif__isString="Hello"),
                                          params))
            res.validate()
            results.append(res.sentiments[0]['marl:hasPolarity'])
        assert 'marl:Positive' in results
        assert 'marl:Negative' in results
