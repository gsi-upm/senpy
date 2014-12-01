from senpy.plugins import SenpyPlugin
from time import sleep

class SleepPlugin(SenpyPlugin):
    def __init__(self, info, *args, **kwargs):
        super(SleepPlugin, self).__init__(info, *args, **kwargs)
        self.timeout = int(info["timeout"])

    def activate(self, *args, **kwargs):
        sleep(self.timeout)
