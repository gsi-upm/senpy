from senpy.plugins import SenpyPlugin

class Prueba(SenpyPlugin):
    def __init__(self, **kwargs):
        super(Prueba, self).__init__(name="prueba",
                                                 version="4.0",
                                                 **kwargs)

plugin = Prueba()
