from senpy.plugins import SenpyPlugin

class DummyPlugin(SenpyPlugin):
    def __init__(self):
        super(DummyPlugin,  self).__init__("dummy")

