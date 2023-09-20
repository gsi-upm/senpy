from senpy.plugins import AnalysisPlugin
from senpy.models import Response, Entry


class ExamplePlugin(AnalysisPlugin):
    '''A *VERY* simple plugin that exemplifies the development of Senpy Plugins'''
    name = "example-plugin"
    author = "@balkian"
    version = "0.1"
    extra_params = {
        "parameter": {
            "@id": "parameter",
            "description": "this parameter does nothing, it is only an example",
            "aliases": ["parameter", "param"],
            "required": True,
            "default": 42
        }
      }
    custom_attribute = "42"

    def analyse_entry(self, entry, activity):
        params = activity.params
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
