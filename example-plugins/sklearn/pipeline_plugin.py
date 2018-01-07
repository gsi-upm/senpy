from senpy import SentimentBox, MappingMixin, easy_test

from mypipeline import pipeline


class PipelineSentiment(MappingMixin, SentimentBox):
    '''
    This is a pipeline plugin that wraps a classifier defined in another module
    (mypipeline).
    '''
    author = '@balkian'
    version = 0.1
    maxPolarityValue = 1
    minPolarityValue = -1

    mappings = {
        1: 'marl:Positive',
        -1: 'marl:Negative'
    }

    def box(self, input, *args, **kwargs):
        return pipeline.predict([input, ])[0]

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
