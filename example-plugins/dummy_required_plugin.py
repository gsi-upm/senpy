from senpy import AnalysisPlugin, easy


class DummyRequired(AnalysisPlugin):
    '''This is a dummy self-contained plugin'''
    author = '@balkian'
    version = '0.1'
    extra_params = {
        'example': {
            'description': 'An example parameter',
            'required': True,
            'options': ['a', 'b']
        }
    }

    def analyse_entry(self, entry, params):
        entry['nif:isString'] = entry['nif:isString'][::-1]
        entry.reversed = entry.get('reversed', 0) + 1
        yield entry

    test_cases = [{
        'entry': {
            'nif:isString': 'Hello',
        },
        'expected': None
    }, {
        'entry': {
            'nif:isString': 'Hello',
        },
        'params': {
            'example': 'a'
        },
        'expected': {
            'nif:isString': 'olleH'
        }
    }]


if __name__ == '__main__':
    easy()
