import os
import logging
logging.basicConfig()
try:
    import unittest.mock as mock
except ImportError:
    import mock
from senpy.extensions import Senpy
from flask import Flask
from flask.ext.testing import TestCase
import unittest

class vaderTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask("test_plugin")
        self.dir = os.path.join(os.path.dirname(__file__))
        self.senpy = Senpy(plugin_folder=self.dir, default_plugins=False)
        self.senpy.init_app(self.app)

    def tearDown(self):
        self.senpy.deactivate_plugin("vaderSentiment", sync=True)

    def test_analyse(self):
        plugin = self.senpy.plugins["vaderSentiment"]
        plugin.activate() 

        texts = {'I am tired :(' : 'marl:Negative',
                 'I love pizza' : 'marl:Positive',
                 'I like going to the cinema :)' : 'marl:Positive',
                 'This cake is disgusting' : 'marl:Negative'}

        for text in texts:
            response = plugin.analyse(input=text)
            expected = texts[text]
            sentimentSet = response.entries[0].sentiments

            max_sentiment = max(sentimentSet, key=lambda x: x['marl:polarityValue'])
            assert max_sentiment['marl:hasPolarity'] == expected

        plugin.deactivate()

if __name__ == '__main__':
    unittest.main()
