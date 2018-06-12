def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    print("Mocking request")
    if args[0] == 'http://api.meaningcloud.com/sentiment-2.1':
        return MockResponse({
            'model': 'general_en',
            'sentence_list': [{
                'text':
                'Hello World',
                'endp':
                '10',
                'inip':
                '0',
                'segment_list': [{
                    'text':
                    'Hello World',
                    'segment_type':
                    'secondary',
                    'confidence':
                    '100',
                    'inip':
                    '0',
                    'agreement':
                    'AGREEMENT',
                    'endp':
                    '10',
                    'polarity_term_list': [],
                    'score_tag':
                    'NONE'
                }],
                'score_tag':
                'NONE',
            }],
            'score_tag':
            'NONE'
        }, 200)
    elif args[0] == 'http://api.meaningcloud.com/topics-2.0':

        return MockResponse({
            'entity_list': [{
                'form':
                'Obama',
                'id':
                '__1265958475430276310',
                'variant_list': [{
                    'endp': '16',
                    'form': 'Obama',
                    'inip': '12'
                }],
                'sementity': {
                    'fiction': 'nonfiction',
                    'confidence': 'uncertain',
                    'class': 'instance',
                    'type': 'Top>Person'
                }
            }],
            'concept_list': [{
                'form':
                'world',
                'id':
                '5c053cd39d',
                'relevance':
                '100',
                'semtheme_list': [{
                    'id': 'ODTHEME_ASTRONOMY',
                    'type': 'Top>NaturalSciences>Astronomy'
                }]
            }],
        }, 200)
    return MockResponse(None, 404)
