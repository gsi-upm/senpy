from future import standard_library
standard_library.install_aliases()


from future.utils import with_metaclass

import os.path
import os
import re
import pickle
import logging
import copy
import pprint

import inspect
import sys
import subprocess
import importlib
import yaml
import threading

from .. import models, utils
from .. import api


logger = logging.getLogger(__name__)

try:
    from gsitk.evaluation.evaluation import Evaluation as Eval
    from sklearn.pipeline import Pipeline
    GSITK_AVAILABLE = True
except ImportError:
    logger.warn('GSITK is not installed. Some functions will be unavailable.')
    GSITK_AVAILABLE = False


class PluginMeta(models.BaseMeta):
    _classes = {}

    def __new__(mcs, name, bases, attrs, **kwargs):
        plugin_type = []
        if hasattr(bases[0], 'plugin_type'):
            plugin_type += bases[0].plugin_type
        plugin_type.append(name)
        alias = attrs.get('name', name)
        attrs['plugin_type'] = plugin_type
        attrs['name'] = alias
        if 'description' not in attrs:
            doc = attrs.get('__doc__', None)
            if doc:
                attrs['description'] = doc
            else:
                logger.warn(('Plugin {} does not have a description. '
                             'Please, add a short summary to help other developers').format(name))
        cls = super(PluginMeta, mcs).__new__(mcs, name, bases, attrs)

        if alias in mcs._classes:
            if os.environ.get('SENPY_TESTING', ""):
                raise Exception(('The type of plugin {} already exists. '
                                'Please, choose a different name').format(name))
            else:
                logger.warn('Overloading plugin class: {}'.format(alias))
        mcs._classes[alias] = cls
        return cls

    @classmethod
    def for_type(cls, ptype):
        return cls._classes[ptype]


class Plugin(with_metaclass(PluginMeta, models.Plugin)):
    '''
    Base class for all plugins in senpy.
    A plugin must provide at least these attributes:

        - version
        - description (or docstring)
        - author

    Additionally, they may provide a URL (url) of a repository or website.

    '''

    def __init__(self, info=None, data_folder=None, **kwargs):
        """
        Provides a canonical name for plugins and serves as base for other
        kinds of plugins.
        """
        logger.debug("Initialising {}".format(info))
        super(Plugin, self).__init__(**kwargs)
        if info:
            self.update(info)
        self.validate()
        self.id = 'plugins/{}_{}'.format(self['name'], self['version'])
        self.is_activated = False
        self._lock = threading.Lock()
        self.data_folder = data_folder or os.getcwd()

    def validate(self):
        missing = []
        for x in ['name', 'description', 'version']:
            if x not in self:
                missing.append(x)
        if missing:
            raise models.Error('Missing configuration parameters: {}'.format(missing))

    def get_folder(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def activate(self):
        pass

    def deactivate(self):
        pass

    def test(self, test_cases=None):
        if not test_cases:
            if not hasattr(self, 'test_cases'):
                raise AttributeError(('Plugin {} [{}] does not have any defined '
                                      'test cases').format(self.id,
                                                           inspect.getfile(self.__class__)))
            test_cases = self.test_cases
        for case in test_cases:
            try:
                self.test_case(case)
                logger.debug('Test case passed:\n{}'.format(pprint.pformat(case)))
            except Exception as ex:
                logger.warn('Test case failed:\n{}'.format(pprint.pformat(case)))
                raise

    def test_case(self, case):
        entry = models.Entry(case['entry'])
        given_parameters = case.get('params', case.get('parameters', {}))
        expected = case.get('expected', None)
        should_fail = case.get('should_fail', False)
        try:
            params = api.parse_params(given_parameters, self.extra_params)
            res = list(self.analyse_entries([entry, ], params))

            if not isinstance(expected, list):
                expected = [expected]
            utils.check_template(res, expected)
            for r in res:
                r.validate()
        except models.Error:
            if should_fail:
                return
            raise
        assert not should_fail

    def open(self, fpath, *args, **kwargs):
        if not os.path.isabs(fpath):
            fpath = os.path.join(self.data_folder, fpath)
        return open(fpath, *args, **kwargs)

    def serve(self, debug=True, **kwargs):
        utils.easy(plugin_list=[self, ], plugin_folder=None, debug=debug, **kwargs)


# For backwards compatibility
SenpyPlugin = Plugin


class Analysis(Plugin):
    '''
    A subclass of Plugin that analyses text and provides an annotation.
    '''

    def analyse(self, *args, **kwargs):
        raise NotImplementedError(
            'Your plugin should implement either analyse or analyse_entry')

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
            results = self.analyse_entry(entry, parameters)
            if inspect.isgenerator(results):
                for result in results:
                    yield result
            else:
                yield results

    def test_case(self, case):
        if 'entry' not in case and 'input' in case:
            entry = models.Entry(_auto_id=False)
            entry.nif__isString = case['input']
            case['entry'] = entry
        super(Analysis, self).test_case(case)


AnalysisPlugin = Analysis


class Conversion(Plugin):
    '''
    A subclass of Plugins that convert between different annotation models.
    e.g. a conversion of emotion models, or normalization of sentiment values.
    '''
    pass


ConversionPlugin = Conversion


class SentimentPlugin(Analysis, models.SentimentPlugin):
    '''
    Sentiment plugins provide sentiment annotation (using Marl)
    '''
    minPolarityValue = 0
    maxPolarityValue = 1

    def test_case(self, case):
        if 'polarity' in case:
            expected = case.get('expected', {})
            s = models.Sentiment(_auto_id=False)
            s.marl__hasPolarity = case['polarity']
            if 'sentiments' not in expected:
                expected['sentiments'] = []
            expected['sentiments'].append(s)
            case['expected'] = expected
        super(SentimentPlugin, self).test_case(case)


class EmotionPlugin(Analysis, models.EmotionPlugin):
    '''
    Emotion plugins provide emotion annotation (using Onyx)
    '''
    minEmotionValue = 0
    maxEmotionValue = 1


class EmotionConversion(Conversion):
    '''
    A subclass of Conversion that converts emotion annotations using different models
    '''
    pass


EmotionConversionPlugin = EmotionConversion


class Box(AnalysisPlugin):
    '''
    Black box plugins delegate analysis to a function.
    The flow is like so:

    .. code-block::

                   entry --> input() --> predict_one() --> output() --> entry'


    In other words: their ``input`` method convers a query (entry and a set of parameters) into
    the input to the box method. The ``output`` method convers the results given by the box into
    an entry that senpy can handle.
    '''

    def input(self, entry, params=None):
        '''Transforms a query (entry+param) into an input for the black box'''
        return entry

    def output(self, output, entry=None, params=None):
        '''Transforms the results of the black box into an entry'''
        return output

    def predict_one(self, input):
        raise NotImplementedError('You should define the behavior of this plugin')

    def analyse_entries(self, entries, params):
        for entry in entries:
            input = self.input(entry=entry, params=params)
            results = self.predict_one(input=input)
            yield self.output(output=results, entry=entry, params=params)

    def fit(self, X=None, y=None):
        return self

    def transform(self, X):
        return [self.predict_one(x) for x in X]

    def predict(self, X):
        return self.transform(X)

    def fit_transform(self, X, y):
        self.fit(X, y)
        return self.transform(X)

    def as_pipe(self):
        pipe = Pipeline([('plugin', self)])
        pipe.name = self.name
        return pipe


class TextBox(Box):
    '''A black box plugin that takes only text as input'''

    def input(self, entry, params):
        entry = super(TextBox, self).input(entry, params)
        return entry['nif:isString']


class SentimentBox(TextBox, SentimentPlugin):
    '''
    A box plugin where the output is only a polarity label or a tuple (polarity, polarityValue)
    '''

    def output(self, output, entry, **kwargs):
        s = models.Sentiment()
        try:
            label, value = output
        except ValueError:
            label, value = output, None
        s.prov(self)
        s.polarity = label
        if value is not None:
            s.polarityValue = value
        entry.sentiments.append(s)
        return entry


class EmotionBox(TextBox, EmotionPlugin):
    '''
    A box plugin where the output is only an a tuple of emotion labels
    '''

    def output(self, output, entry, **kwargs):
        if not isinstance(output, list):
            output = [output]
        s = models.EmotionSet()
        entry.emotions.append(s)
        for label in output:
            e = models.Emotion(onyx__hasEmotionCategory=label)
            s.append(e)
        return entry


class MappingMixin(object):

    @property
    def mappings(self):
        return self._mappings

    @mappings.setter
    def mappings(self, value):
        self._mappings = value

    def output(self, output, entry, params):
        output = self.mappings.get(output,
                                   self.mappings.get('default', output))
        return super(MappingMixin, self).output(output=output,
                                                entry=entry,
                                                params=params)


class ShelfMixin(object):
    @property
    def sh(self):
        if not hasattr(self, '_sh') or self._sh is None:
            self._sh = {}
            if os.path.isfile(self.shelf_file):
                try:
                    with self.open(self.shelf_file, 'rb') as p:
                        self._sh = pickle.load(p)
                except (IndexError, EOFError, pickle.UnpicklingError):
                    logger.warning('{} has a corrupted shelf file!'.format(self.id))
                    if not self.get('force_shelf', False):
                        raise
        return self._sh

    @sh.deleter
    def sh(self):
        if os.path.isfile(self.shelf_file):
            os.remove(self.shelf_file)
            del self._sh
        self.save()

    @sh.setter
    def sh(self, value):
        self._sh = value

    @property
    def shelf_file(self):
        if not hasattr(self, '_shelf_file') or not self._shelf_file:
            self._shelf_file = os.path.join(self.data_folder, self.name + '.p')
        return self._shelf_file

    @shelf_file.setter
    def shelf_file(self, value):
        self._shelf_file = value

    def save(self):
        logger.debug('saving pickle')
        if hasattr(self, '_sh') and self._sh is not None:
            with self.open(self.shelf_file, 'wb') as f:
                pickle.dump(self._sh, f)


def pfilter(plugins, **kwargs):
    """ Filter plugins by different criteria """
    if isinstance(plugins, models.Plugins):
        plugins = plugins.plugins
    elif isinstance(plugins, dict):
        plugins = plugins.values()
    ptype = kwargs.pop('plugin_type', Plugin)
    logger.debug('#' * 100)
    logger.debug('ptype {}'.format(ptype))
    if ptype:
        if isinstance(ptype, PluginMeta):
            ptype = ptype.__name__
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
    return candidates


def load_module(name, root=None):
    if root:
        sys.path.append(root)
    tmp = importlib.import_module(name)
    if root:
        sys.path.remove(root)
    return tmp


def _log_subprocess_output(process):
    for line in iter(process.stdout.readline, b''):
        logger.info('%r', line)
    for line in iter(process.stderr.readline, b''):
        logger.error('%r', line)


def install_deps(*plugins):
    installed = False
    for info in plugins:
        requirements = info.get('requirements', [])
        if requirements:
            pip_args = [sys.executable, '-m', 'pip', 'install']
            for req in requirements:
                pip_args.append(req)
            logger.info('Installing requirements: ' + str(requirements))
            process = subprocess.Popen(pip_args,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            _log_subprocess_output(process)
            exitcode = process.wait()
            installed = True
            if exitcode != 0:
                raise models.Error("Dependencies not properly installed")
    return installed


is_plugin_file = re.compile(r'.*\.senpy$|senpy_[a-zA-Z0-9_]+\.py$|'
                            '^(?!test_)[a-zA-Z0-9_]+_plugin.py$')


def find_plugins(folders):
    for search_folder in folders:
        for root, dirnames, filenames in os.walk(search_folder):
            # Do not look for plugins in hidden or special folders
            dirnames[:] = [d for d in dirnames if d[0] not in ['.', '_']]
            for filename in filter(is_plugin_file.match, filenames):
                fpath = os.path.join(root, filename)
                yield fpath


def from_path(fpath, **kwargs):
    logger.debug("Loading plugin from {}".format(fpath))
    if fpath.endswith('.py'):
        # We asume root is the dir of the file, and module is the name of the file
        root = os.path.dirname(fpath)
        module = os.path.basename(fpath)[:-3]
        for instance in _from_module_name(module=module, root=root, **kwargs):
            yield instance
    else:
        info = parse_plugin_info(fpath)
        yield from_info(info, **kwargs)


def from_folder(folders, loader=from_path, **kwargs):
    plugins = []
    for fpath in find_plugins(folders):
        for plugin in loader(fpath, **kwargs):
            plugins.append(plugin)
    return plugins


def from_info(info, root=None, **kwargs):
    if any(x not in info for x in ('module',)):
        raise ValueError('Plugin info is not valid: {}'.format(info))
    module = info["module"]

    if not root and '_path' in info:
        root = os.path.dirname(info['_path'])

    return one_from_module(module, root=root, info=info, **kwargs)


def parse_plugin_info(fpath):
    logger.debug("Parsing plugin info: {}".format(fpath))
    with open(fpath, 'r') as f:
        info = yaml.load(f)
    info['_path'] = fpath
    return info


def from_module(module, **kwargs):

    if inspect.ismodule(module):
        res = _from_loaded_module(module, **kwargs)
    else:
        res = _from_module_name(module, **kwargs)
    for p in res:
        yield p


def one_from_module(module, root, info, **kwargs):
    if '@type' in info:
        cls = PluginMeta.from_type(info['@type'])
        return cls(info=info, **kwargs)
    instance = next(from_module(module=module, root=root, info=info, **kwargs), None)
    if not instance:
        raise Exception("No valid plugin for: {}".format(module))
    return instance


def _classes_in_module(module):
    for _, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and inspect.getmodule(obj) == module:
            logger.debug(("Found plugin class:"
                          " {}@{}").format(obj, inspect.getmodule(obj)))
            yield obj


def _instances_in_module(module):
    for _, obj in inspect.getmembers(module):
        if isinstance(obj, Plugin) and inspect.getmodule(obj) == module:
            logger.debug(("Found plugin instance:"
                          " {}@{}").format(obj, inspect.getmodule(obj)))
            yield obj


def _from_module_name(module, root, info=None, install=True, **kwargs):
    try:
        module = load_module(module, root)
    except ImportError:
        if not install or not info:
            raise
        install_deps(info)
        module = load_module(module, root)
    for plugin in _from_loaded_module(module=module, root=root, info=info, **kwargs):
        yield plugin


def _from_loaded_module(module, info=None, **kwargs):
    for cls in _classes_in_module(module):
        yield cls(info=info, **kwargs)
    for instance in _instances_in_module(module):
        yield instance


def evaluate(plugins, datasets, **kwargs):
    if not GSITK_AVAILABLE:
        raise Exception('GSITK is not available. Install it to use this function.')

    ev = Eval(tuples=None,
              datasets=datasets,
              pipelines=[plugin.as_pipe() for plugin in plugins])
    ev.evaluate()
    results = ev.results
    evaluations = evaluations_to_JSONLD(results, **kwargs)
    return evaluations


def evaluations_to_JSONLD(results, flatten=False):
    '''
    Map the evaluation results to a JSONLD scheme
    '''

    evaluations = list()
    metric_names = ['accuracy', 'precision_macro', 'recall_macro',
                    'f1_macro', 'f1_weighted', 'f1_micro', 'f1_macro']

    for index, row in results.iterrows():
        evaluation = models.Evaluation()
        if row.get('CV', True):
            evaluation['@type'] = ['StaticCV', 'Evaluation']
        evaluation.evaluatesOn = row['Dataset']
        evaluation.evaluates = row['Model']
        i = 0
        if flatten:
            metric = models.Metric()
            for name in metric_names:
                metric[name] = row[name]
            evaluation.metrics.append(metric)
        else:
            # We should probably discontinue this representation
            for name in metric_names:
                metric = models.Metric()
                metric['@id'] = 'Metric' + str(i)
                metric['@type'] = name.capitalize()
                metric.value = row[name]
                evaluation.metrics.append(metric)
                i += 1
        evaluations.append(evaluation)
    return evaluations
