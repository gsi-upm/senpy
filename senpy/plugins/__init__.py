from future import standard_library
standard_library.install_aliases()

import inspect
import os.path
import os
import pickle
import logging
import tempfile
import copy
from .. import models
from ..api import API_PARAMS

logger = logging.getLogger(__name__)


class Plugin(models.Plugin):
    def __init__(self, info=None):
        """
        Provides a canonical name for plugins and serves as base for other
        kinds of plugins.
        """
        if not info:
            raise models.Error(message=("You need to provide configuration"
                                        "information for the plugin."))
        logger.debug("Initialising {}".format(info))
        id = 'plugins/{}_{}'.format(info['name'], info['version'])
        super(Plugin, self).__init__(id=id, **info)
        self.is_activated = False

    def get_folder(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def activate(self):
        pass

    def deactivate(self):
        pass


SenpyPlugin = Plugin


class AnalysisPlugin(Plugin):

    def analyse(self, *args, **kwargs):
        raise NotImplemented(
            'Your method should implement either analyse or analyse_entry')

    def analyse_entry(self, entry, parameters):
        """ An implemented plugin should override this method.
        This base method is here to adapt old style plugins which only
        implement the *analyse* function.
        Note that this method may yield an annotated entry or a list of
        entries (e.g. in a tokenizer)
        """
        text = entry['text']
        params = copy.copy(parameters)
        params['input'] = text
        results = self.analyse(**params)
        for i in results.entries:
            yield i

    def analyse_entries(self, entries, parameters):
        for entry in entries:
            logger.debug('Analysing entry with plugin {}: {}'.format(self, entry))
            for result in self.analyse_entry(entry, parameters):
                yield result


class ConversionPlugin(Plugin):
    pass


class SentimentPlugin(models.SentimentPlugin, AnalysisPlugin):
    def __init__(self, info, *args, **kwargs):
        super(SentimentPlugin, self).__init__(info, *args, **kwargs)
        self.minPolarityValue = float(info.get("minPolarityValue", 0))
        self.maxPolarityValue = float(info.get("maxPolarityValue", 1))


class EmotionPlugin(models.EmotionPlugin, AnalysisPlugin):
    def __init__(self, info, *args, **kwargs):
        super(EmotionPlugin, self).__init__(info, *args, **kwargs)
        self.minEmotionValue = float(info.get("minEmotionValue", -1))
        self.maxEmotionValue = float(info.get("maxEmotionValue", 1))


class EmotionConversionPlugin(models.EmotionConversionPlugin, ConversionPlugin):
    pass


class ShelfMixin(object):
    @property
    def sh(self):
        if not hasattr(self, '_sh') or self._sh is None:
            self.__dict__['_sh'] = {}
            if os.path.isfile(self.shelf_file):
                try:
                    self.__dict__['_sh'] = pickle.load(open(self.shelf_file, 'rb'))
                except (IndexError, EOFError, pickle.UnpicklingError):
                    logger.warning('{} has a corrupted shelf file!'.format(self.id))
                    if not self.get('force_shelf', False):
                        raise
        return self._sh

    @sh.deleter
    def sh(self):
        if os.path.isfile(self.shelf_file):
            os.remove(self.shelf_file)
            del self.__dict__['_sh']
        self.save()

    @property
    def shelf_file(self):
        if 'shelf_file' not in self or not self['shelf_file']:
            sd = os.environ.get('SENPY_DATA', tempfile.gettempdir())
            self.shelf_file = os.path.join(sd, self.name + '.p')
        return self['shelf_file']

    def save(self):
        logger.debug('saving pickle')
        if hasattr(self, '_sh') and self._sh is not None:
            with open(self.shelf_file, 'wb') as f:
                pickle.dump(self._sh, f)


default_plugin_type = API_PARAMS['plugin_type']['default']


def pfilter(plugins, **kwargs):
    """ Filter plugins by different criteria """
    if isinstance(plugins, models.Plugins):
        plugins = plugins.plugins
    elif isinstance(plugins, dict):
        plugins = plugins.values()
    ptype = kwargs.pop('plugin_type', default_plugin_type)
    logger.debug('#' * 100)
    logger.debug('ptype {}'.format(ptype))
    if ptype:
        try:
            ptype = ptype[0].upper() + ptype[1:]
            pclass = globals()[ptype]
            logger.debug('Class: {}'.format(pclass))
            candidates = filter(lambda x: isinstance(x, pclass),
                                plugins)
        except KeyError:
            raise models.Error('{} is not a valid type'.format(ptype))
    else:
        candidates = plugins

    logger.debug(candidates)

    def matches(plug):
        res = all(getattr(plug, k, None) == v for (k, v) in kwargs.items())
        logger.debug(
            "matching {} with {}: {}".format(plug.name, kwargs, res))
        return res

    if kwargs:
        candidates = filter(matches, candidates)
    return {p.name: p for p in candidates}
