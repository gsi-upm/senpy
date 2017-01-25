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

class SentiTextTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask("test_plugin")
        self.dir = os.path.join(os.path.dirname(__file__))
        self.senpy = Senpy(plugin_folder=self.dir, default_plugins=False)
        self.senpy.init_app(self.app)

    def tearDown(self):
        self.senpy.deactivate_plugin("SentiText", sync=True)

    def test_analyse(self):
        plugin = self.senpy.plugins["SentiText"]
        plugin.activate()

        texts = {'Odio ir al cine' :  'marl:Neutral',
                 'El cielo esta nublado' : 'marl:Positive',
                 'Esta tarta esta muy buena' : 'marl:Neutral'}

        for text in texts:
            response = plugin.analyse(input=text)
            sentimentSet = response.entries[0].sentiments[0]
            print sentimentSet
            expected = texts[text]
            
            assert sentimentSet['marl:hasPolarity'] == expected
        
        plugin.deactivate()

if __name__ == '__main__':
    unittest.main()