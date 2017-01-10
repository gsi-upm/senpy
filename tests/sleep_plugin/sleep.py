from senpy.plugins import SenpyPlugin
from senpy.models import Results
from time import sleep


class SleepPlugin(SenpyPlugin):
    def activate(self, *args, **kwargs):
        sleep(self.timeout)

    def analyse(self, *args, **kwargs):
        sleep(float(kwargs.get("timeout", self.timeout)))
        return Results()
