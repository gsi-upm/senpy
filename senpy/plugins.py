from future import standard_library
standard_library.install_aliases()

import inspect
import os.path
import pickle
import logging
from .models import Response, PluginModel, Error

logger = logging.getLogger(__name__)

class SenpyPlugin(PluginModel):

    def __init__(self, info=None):
        if not info:
            raise Error(message=("You need to provide configuration"
                                 "information for the plugin."))
        logger.debug("Initialising {}".format(info))
        super(SenpyPlugin, self).__init__(info)
        self.id = '{}_{}'.format(self.name, self.version)
        self._info = info
        self.is_activated = False

    def get_folder(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def analyse(self, *args, **kwargs):
        logger.debug("Analysing with: {} {}".format(self.name, self.version))
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass

    def __del__(self):
        ''' Destructor, to make sure all the resources are freed '''
        self.deactivate()

class SentimentPlugin(SenpyPlugin):

    def __init__(self, info, *args, **kwargs):
        super(SentimentPlugin, self).__init__(info, *args, **kwargs)
        self.minPolarityValue = float(info.get("minPolarityValue", 0))
        self.maxPolarityValue = float(info.get("maxPolarityValue", 1))
        self["@type"] = "marl:SentimentAnalysis"


class EmotionPlugin(SenpyPlugin):

    def __init__(self, info, *args, **kwargs):
        resp = super(EmotionPlugin, self).__init__(info, *args, **kwargs)
        self.minEmotionValue = float(info.get("minEmotionValue", 0))
        self.maxEmotionValue = float(info.get("maxEmotionValue", 0))
        self["@type"] = "onyx:EmotionAnalysis"


class ShelfMixin(object):

    @property
    def sh(self):
        if not hasattr(self, '_sh') or self._sh is None:
            self.__dict__['_sh'] = {}
            if os.path.isfile(self.shelf_file):
                self.__dict__['_sh'] = pickle.load(open(self.shelf_file, 'rb'))
        return self._sh

    @sh.deleter
    def sh(self):
        if os.path.isfile(self.shelf_file):
            os.remove(self.shelf_file)
            del self.__dict__['_sh']
        self.save()

    def __del__(self):
        self.save()        
        super(ShelfMixin, self).__del__()

    @property
    def shelf_file(self):
        if not hasattr(self, '_shelf_file') or not self._shelf_file:
            if hasattr(self, '_info') and 'shelf_file' in self._info:
                self.__dict__['_shelf_file'] = self._info['shelf_file']
            else:
                self._shelf_file = os.path.join(self.get_folder(), self.name + '.p')
        return self._shelf_file 

    def save(self):
        logger.debug('closing pickle')
        if hasattr(self, '_sh') and self._sh is not None:
            with open(self.shelf_file, 'wb') as f:
                pickle.dump(self._sh, f)
        del(self.__dict__['_sh'])
