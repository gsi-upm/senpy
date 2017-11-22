from future import standard_library
standard_library.install_aliases()

import os.path
import os
import pickle
import logging
import copy

import fnmatch
import inspect
import sys
import subprocess
import importlib
import yaml
import threading

from contextlib import contextmanager

from .. import models, utils
from ..api import API_PARAMS

logger = logging.getLogger(__name__)


class Plugin(models.Plugin):
    def __init__(self, info=None, data_folder=None):
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
        self._lock = threading.Lock()
        self.data_folder = data_folder or os.getcwd()

    def get_folder(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def activate(self):
        pass

    def deactivate(self):
        pass

    def test(self):
        if not hasattr(self, 'test_cases'):
            import inspect
            raise AttributeError(('Plugin {} [{}] does not have any defined '
                                  'test cases').format(self.id, inspect.getfile(self.__class__)))
        for case in self.test_cases:
            res = list(self.analyse_entry(models.Entry(case['entry']),
                                          case['params']))
            exp = case['expected']
            if not isinstance(exp, list):
                exp = [exp]
            utils.check_template(res, exp)
            for r in res:
                r.validate()

    @contextmanager
    def open(self, fpath, *args, **kwargs):
        if not os.path.isabs(fpath):
            fpath = os.path.join(self.data_folder, fpath)
        with open(fpath, *args, **kwargs) as f:
            yield f


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
        text = entry['nif:isString']
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
                    with self.open(self.shelf_file, 'rb') as p:
                        self.__dict__['_sh'] = pickle.load(p)
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
            self.shelf_file = os.path.join(self.data_folder, self.name + '.p')
        return self['shelf_file']

    def save(self):
        logger.debug('saving pickle')
        if hasattr(self, '_sh') and self._sh is not None:
            with self.open(self.shelf_file, 'wb') as f:
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


def validate_info(info):
    return all(x in info for x in ('name', 'module', 'description', 'version'))


def load_module(name, root=None):
    if root:
        sys.path.append(root)
    tmp = importlib.import_module(name)
    if root:
        sys.path.remove(root)
    return tmp


def log_subprocess_output(process):
    for line in iter(process.stdout.readline, b''):
        logger.info('%r', line)
    for line in iter(process.stderr.readline, b''):
        logger.error('%r', line)


def install_deps(*plugins):
    installed = False
    for info in plugins:
        requirements = info.get('requirements', [])
        if requirements:
            pip_args = [sys.executable, '-m', 'pip', 'install', '--use-wheel']
            for req in requirements:
                pip_args.append(req)
            logger.info('Installing requirements: ' + str(requirements))
            process = subprocess.Popen(pip_args,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            log_subprocess_output(process)
            exitcode = process.wait()
            installed = True
            if exitcode != 0:
                raise models.Error("Dependencies not properly installed")
    return installed


def load_plugin_from_info(info, root=None, validator=validate_info, install=True, *args, **kwargs):
    if not root and '_path' in info:
        root = os.path.dirname(info['_path'])
    if not validator(info):
        raise ValueError('Plugin info is not valid: {}'.format(info))
    module = info["module"]

    try:
        tmp = load_module(module, root)
    except ImportError:
        if not install:
            raise
        install_deps(info)
        tmp = load_module(module, root)
    candidate = None
    for _, obj in inspect.getmembers(tmp):
        if inspect.isclass(obj) and inspect.getmodule(obj) == tmp:
            logger.debug(("Found plugin class:"
                          " {}@{}").format(obj, inspect.getmodule(obj)))
            candidate = obj
            break
    if not candidate:
        logger.debug("No valid plugin for: {}".format(module))
        return
    module = candidate(info=info, *args, **kwargs)
    return module


def parse_plugin_info(fpath):
    logger.debug("Loading plugin: {}".format(fpath))
    with open(fpath, 'r') as f:
        info = yaml.load(f)
    info['_path'] = fpath
    name = info['name']
    return name, info


def load_plugin(fpath, *args, **kwargs):
    name, info = parse_plugin_info(fpath)
    logger.debug("Info: {}".format(info))
    plugin = load_plugin_from_info(info, *args, **kwargs)
    return name, plugin


def load_plugins(folders, loader=load_plugin, *args, **kwargs):
    plugins = {}
    for search_folder in folders:
        for root, dirnames, filenames in os.walk(search_folder):
            # Do not look for plugins in hidden or special folders
            dirnames[:] = [d for d in dirnames if d[0] not in ['.', '_']]
            for filename in fnmatch.filter(filenames, '*.senpy'):
                fpath = os.path.join(root, filename)
                name, plugin = loader(fpath, *args, **kwargs)
                if plugin and name:
                    plugins[name] = plugin
    return plugins
