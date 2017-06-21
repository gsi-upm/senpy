from senpy.plugins import AnalysisPlugin
from senpy.models import Entry
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.tokenize.simple import LineTokenizer
import nltk


class SplitPlugin(AnalysisPlugin):

    def activate(self):
        nltk.download('punkt')

    def analyse_entry(self, entry, params):
        chunker_type = params.get("delimiter", "sentence")
        original_text = entry.get('nif:isString', None)
        if chunker_type == "sentence":
            tokenizer = PunktSentenceTokenizer()
        if chunker_type == "paragraph":
            tokenizer = LineTokenizer()
        chars = tokenizer.span_tokenize(original_text)
        for i, chunk in enumerate(tokenizer.tokenize(original_text)):
            e = Entry()
            e['nif:isString'] = chunk
            if entry.id:
                e.id = entry.id + "#char={},{}".format(chars[i][0], chars[i][1])
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
                "id": ":test",
                'nif:isString': 'Hello. World.'
            },
            'params': {
                'delimiter': 'sentence',
            },
            'expected': [
                {
                    "@id": ":test#char=0,6",
                    'nif:isString': 'Hello.'
                },
                {
                    "@id": ":test#char=7,13",
                    'nif:isString': 'World.'
                }
            ]
        }
    ]
