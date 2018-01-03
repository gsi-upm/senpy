from senpy.plugins import AnalysisPlugin
from time import sleep


class Sleep(AnalysisPlugin):
    '''Dummy plugin to test async'''
    author = "@balkian"
    version = "0.2"
    timeout = 0.05
    extra_params = {
        "timeout": {
            "@id": "timeout_sleep",
            "aliases": ["timeout", "to"],
            "required": False,
            "default": 0
        }
    }

    def activate(self, *args, **kwargs):
        sleep(self.timeout)

    def analyse_entry(self, entry, params):
        sleep(float(params.get("timeout", self.timeout)))
        yield entry

    def test(self):
        pass
