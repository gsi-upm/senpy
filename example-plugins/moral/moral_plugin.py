from senpy.ns import amor, amor_bhv, amor_mft, prov
from senpy.plugins import MoralityPlugin


class DummyMoralityPlugin(MoralityPlugin):
    moralValueModel: str = amor_mft["MoralFoundationTHeory"]

    def annotate(self, entry, activity, **kwargs):
        yield MoralAnnotation(amor_bhv['Conservation'],
                              confidence=1.8)
