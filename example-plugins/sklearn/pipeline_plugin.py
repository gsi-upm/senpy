from senpy import SentimentBox, easy_test

from mypipeline import pipeline


class PipelineSentiment(SentimentBox):
    '''This is a pipeline plugin that wraps a classifier defined in another module
(mypipeline).'''
    author = '@balkian'
    version = 0.1
    maxPolarityValue = 1
    minPolarityValue = -1

    def predict_one(self, features, **kwargs):
        if pipeline.predict(features) > 0:
            return [1, 0, 0]
        return [0, 0, 1]

    test_cases = [
        {
            'input': 'The sentiment for senpy should be positive :)',
            'polarity': 'marl:Positive'
        },
        {
            'input': 'The sentiment for senpy should be negative :(',
            'polarity': 'marl:Negative'
        }
    ]


if __name__ == '__main__':
    easy_test()
