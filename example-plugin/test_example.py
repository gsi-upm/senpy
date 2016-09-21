import unittest
from flask import Flask
import os

from senpy.extensions import Senpy

class emoTextWAFTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask("Example")
        self.dir = os.path.join(os.path.dirname(__file__))
        self.senpy = Senpy(plugin_folder=self.dir, default_plugins=False)
        self.senpy.init_app(self.app)

    def tearDown(self):
        self.senpy.deactivate_plugin("ExamplePlugin", sync=True)

    def test_analyse(self):
        assert len(self.senpy.plugins.keys()) == 1
        assert True

if __name__ == '__main__':
    unittest.main()
