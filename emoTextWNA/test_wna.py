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

class emoTextWAFTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask("test_plugin")
        self.dir = os.path.join(os.path.dirname(__file__))
        self.senpy = Senpy(plugin_folder=self.dir, default_plugins=False)
        self.senpy.init_app(self.app)

    def tearDown(self):
        self.senpy.deactivate_plugin("EmoTextWAF", sync=True)

    def test_analyse(self):
        plugin = self.senpy.plugins["EmoTextWAF"]
        plugin.activate()

        texts = {'I hate you': 'anger',
                 'i am sad': 'sadness',
                 'i am happy with my marks': 'joy',
                 'This movie is scary': 'negative-fear'}

        for text in texts:
            response = plugin.analyse(input=text)
            expected = texts[text]
            emotionSet = response.entries[0].emotions[0]
            max_emotion = max(emotionSet['onyx:hasEmotion'], key=lambda x: x['onyx:hasEmotionIntensity'])
            assert max_emotion['onyx:hasEmotionCategory'] == expected

        plugin.deactivate()

if __name__ == '__main__':
    unittest.main()
