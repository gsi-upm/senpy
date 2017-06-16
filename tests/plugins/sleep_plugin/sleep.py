from senpy.plugins import AnalysisPlugin
from time import sleep


class SleepPlugin(AnalysisPlugin):
    def activate(self, *args, **kwargs):
        sleep(self.timeout)

    def analyse_entry(self, entry, params):
        sleep(float(params.get("timeout", self.timeout)))
        yield entry

    def test(self):
        pass
