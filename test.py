import os
import logging
logging.basicConfig()
try:
    import unittest.mock as mock
except ImportError:
    import mock
from senpy.extensions import Senpy
from flask import Flask
import unittest
import re

class emoTextANEWTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask("test_plugin")
        self.dir = os.path.join(os.path.dirname(__file__))
        self.senpy = Senpy(plugin_folder=self.dir, default_plugins=False)
        self.senpy.init_app(self.app)

    def tearDown(self):
        self.senpy.deactivate_plugin("EmoTextANEW", sync=True)

    def test_analyse(self):
        plugin = self.senpy.plugins["EmoTextANEW"]
        plugin.activate()

        ontology = "http://gsi.dit.upm.es/ontologies/wnaffect/ns#"
        texts = {'I hate you': 'anger',
                 'i am sad': 'sadness',
                 'i am happy with my marks': 'joy',
                 'This movie is scary': 'negative-fear',
                 'this cake is disgusting' : 'negative-fear'}

        for text in texts:
            response = plugin.analyse(input=text)
            expected = texts[text]
            emotionSet = response.entries[0].emotions[0]

            assert emotionSet['onyx:hasEmotion'][0]['onyx:hasEmotionCategory'] == ontology+expected

        plugin.deactivate()

if __name__ == '__main__':
    unittest.main()
