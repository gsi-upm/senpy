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
        original_id = entry.id
        original_text = entry.get("text", None)
        if chunker_type == "sentence":
            tokenizer = PunktSentenceTokenizer()
            chars = tokenizer.span_tokenize(original_text)
            for i, sentence in enumerate(tokenizer.tokenize(original_text)):
                e = Entry()
                e.text = sentence
                e.id = original_id + "#char={},{}".format(chars[i][0], chars[i][1])
                yield e
        if chunker_type == "paragraph":
            tokenizer = LineTokenizer()
            chars = tokenizer.span_tokenize(original_text)
            for i, paragraph in enumerate(tokenizer.tokenize(original_text)):
                e = Entry() 
                e.text = paragraph
                chars = [char for char in chars]
                e.id = original_id + "#char={},{}".format(chars[i][0], chars[i][1])
                yield e
