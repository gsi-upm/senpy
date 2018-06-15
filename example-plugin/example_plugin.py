from senpy.plugins import Analysis
from senpy.models import Response, Entry


class ExamplePlugin(Analysis):
    '''A *VERY* simple plugin that exemplifies the development of Senpy Plugins'''
    name = "example-plugin"
    author = "@balkian"
    version = "0.1"
    extra_params = {
        "parameter": {
            "@id": "parameter",
            "aliases": ["parameter", "param"],
            "required": True,
            "default": 42
        }
      }
    custom_attribute = "42"

    def analyse_entry(self, entry, params):
        self.log.debug('Analysing with the example.')
        self.log.debug('The answer to this response is: %s.' % params['parameter'])
        resp = Response()
        entry['example:reversed'] = entry.text[::-1]
        entry['example:the_answer'] = params['parameter']

        yield entry

    test_cases = [{
        'input': 'hello',
        'expected': {
            'example:reversed': 'olleh'
        }
    }]
