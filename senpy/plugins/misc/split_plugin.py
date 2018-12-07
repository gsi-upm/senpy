from senpy.plugins import AnalysisPlugin
from senpy.models import Entry
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.tokenize.simple import LineTokenizer
import nltk


class Split(AnalysisPlugin):
    '''description: A sample plugin that chunks input text'''

    author = ["@militarpancho", '@balkian']
    version = '0.3'
    url = "https://github.com/gsi-upm/senpy"

    extra_params = {
        'delimiter': {
            'aliases': ['type', 't'],
            'required': False,
            'default': 'sentence',
            'options': ['sentence', 'paragraph']
        },
    }

    def activate(self):
        nltk.download('punkt')

    def analyse_entry(self, entry, params):
        yield entry
        chunker_type = params["delimiter"]
        original_text = entry['nif:isString']
        if chunker_type == "sentence":
            tokenizer = PunktSentenceTokenizer()
        if chunker_type == "paragraph":
            tokenizer = LineTokenizer()
        chars = list(tokenizer.span_tokenize(original_text))
        if len(chars) == 1:
            # This sentence was already split
            return
        for i, chunk in enumerate(chars):
            start, end = chunk
            e = Entry()
            e['nif:isString'] = original_text[start:end]
            if entry.id:
                e.id = entry.id + "#char={},{}".format(start, end)
            yield e

    test_cases = [
        {
            'entry': {
                'nif:isString': 'Hello. World.'
            },
            'params': {
                'delimiter': 'sentence',
            },
            'expected': [
                {
                    'nif:isString': 'Hello.'
                },
                {
                    'nif:isString': 'World.'
                }
            ]
        },
        {
            'entry': {
                "@id": ":test",
                'nif:isString': 'Hello\nWorld'
            },
            'params': {
                'delimiter': 'paragraph',
            },
            'expected': [
                {
                    "@id": ":test#char=0,5",
                    'nif:isString': 'Hello'
                },
                {
                    "@id": ":test#char=6,11",
                    'nif:isString': 'World'
                }
            ]
        }
    ]
