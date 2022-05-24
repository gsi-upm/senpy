#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

from future import standard_library
standard_library.install_aliases()

from future.utils import with_metaclass
from functools import partial

import os.path
import os
import re
import pickle
import logging
import pprint

import inspect
import sys
import subprocess
import importlib
import yaml
import threading
import multiprocessing
import pkg_resources
from nltk import download
from textwrap import dedent
from sklearn.base import TransformerMixin, BaseEstimator
from itertools import product

from .. import models, utils
from .. import api
from .. import gsitk_compat
from .. import testing

logger = logging.getLogger(__name__)


class PluginMeta(models.BaseMeta):
    _classes = {}

    def __new__(mcs, name, bases, attrs, **kwargs):
        plugin_type = set()
        for base in bases:
            if hasattr(base, '_plugin_type'):
                plugin_type |= base._plugin_type
        plugin_type.add(name)
        alias = attrs.get('name', name).lower()
        attrs['_plugin_type'] = plugin_type
        logger.debug('Adding new plugin class: %s %s %s %s', name, bases, attrs, plugin_type)
        attrs['name'] = alias
        if 'description' not in attrs:
            doc = attrs.get('__doc__', None)
            if doc:
                attrs['description'] = dedent(doc)
            else:
                logger.warning(
                    ('Plugin {} does not have a description. '
                     'Please, add a short summary to help other developers'
                     ).format(name))
        cls = super(PluginMeta, mcs).__new__(mcs, name, bases, attrs)

        if alias in mcs._classes:
            if os.environ.get('SENPY_TESTING', ""):
                raise Exception(
                    ('The type of plugin {} already exists. '
                     'Please, choose a different name').format(name))
            else:
                logger.warning('Overloading plugin class: {}'.format(alias))
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

    _terse_keys = ['name', '@id', '@type', 'author', 'description',
                   'extra_params', 'is_activated', 'url', 'version']

    def __init__(self, info=None, data_folder=None, **kwargs):
        """
        Provides a canonical name for plugins and serves as base for other
        kinds of plugins.
        """
        logger.debug("Initialising %s", info)
        super(Plugin, self).__init__(**kwargs)
        if info:
            self.update(info)
        self.validate()
        self.id = 'endpoint:plugins/{}_{}'.format(self['name'],
                                                  self['version'])
        self.is_activated = False
        self._lock = threading.Lock()
        self._directory = os.path.abspath(
            os.path.dirname(inspect.getfile(self.__class__)))

        data_folder = data_folder or os.getcwd()
        subdir = os.path.join(data_folder, self.name)

        self._data_paths = [
            data_folder,
            subdir,
            self._directory,
            os.path.join(self._directory, 'data'),
        ]

        if os.path.exists(subdir):
            data_folder = subdir
        self.data_folder = data_folder

        self._log = logging.getLogger('{}.{}'.format(__name__, self.name))

    @property
    def log(self):
        return self._log

    def validate(self):
        missing = []
        for x in ['name', 'description', 'version']:
            if x not in self:
                missing.append(x)
        if missing:
            raise models.Error(
                'Missing configuration parameters: {}'.format(missing))

    def get_folder(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def _activate(self):
        self.activate()
        self.is_activated = True

    def _deactivate(self):
        self.is_activated = False
        self.deactivate()

    def activate(self):
        pass

    def deactivate(self):
        pass

    def process(self, request, activity, **kwargs):
        """
        An implemented plugin should override this method.
        Here, we assume that a process_entries method exists.
        """
        newentries = list(
            self.process_entries(request.entries, activity))
        request.entries = newentries
        return request

    def process_entries(self, entries, activity):
        for entry in entries:
            self.log.debug('Processing entry with plugin %s: %s', self, entry)
            results = self.process_entry(entry, activity)
            if inspect.isgenerator(results):
                for result in results:
                    yield result
            else:
                yield results

    def process_entry(self, entry, activity):
        """
        This base method is here to adapt plugins which only
        implement the *process* function.
        Note that this method may yield an annotated entry or a list of
        entries (e.g. in a tokenizer)
        """
        raise NotImplementedError(
            'You need to implement process, process_entries or process_entry in your plugin'
        )

    def test(self, test_cases=None):
        if not self.is_activated:
            self._activate()
        if not test_cases:
            if not hasattr(self, 'test_cases'):
                raise AttributeError(
                    ('Plugin {} [{}] does not have any defined '
                     'test cases').format(self.id,
                                          inspect.getfile(self.__class__)))
            test_cases = self.test_cases
        for case in test_cases:
            try:
                fmt = 'case: {}'.format(case.get('name', case))
                if 'name' in case:
                    self.log.info('Test case: {}'.format(case['name']))
                self.log.debug('Test case:\n\t{}'.format(
                    pprint.pformat(fmt)))
                self.test_case(case)
            except Exception as ex:
                self.log.warning('Test case failed:\n{}'.format(
                    pprint.pformat(case)))
                raise

    def test_case(self, case, mock=testing.MOCK_REQUESTS):
        if 'entry' not in case and 'input' in case:
            entry = models.Entry(_auto_id=False)
            entry.nif__isString = case['input']
            case['entry'] = entry
        entry = models.Entry(case['entry'])
        given_parameters = case.get('params', case.get('parameters', {}))
        expected = case.get('expected', None)
        should_fail = case.get('should_fail', False)
        responses = case.get('responses', [])

        try:
            request = models.Response()
            parameters = api.parse_params(given_parameters,
                                          self.extra_params)
            request.entries = [
                entry,
            ]

            activity = self.activity(parameters)

            method = partial(self.process, request, activity)

            if mock:
                res = method()
            else:
                with testing.patch_all_requests(responses):
                    res = method()

            if not isinstance(expected, list):
                expected = [expected]
            utils.check_template(res.entries, expected)
            res.validate()
        except models.Error:
            if should_fail:
                return
            raise
        assert not should_fail

    def find_file(self, fname):
        for p in self._data_paths:
            alternative = os.path.join(p, fname)
            if os.path.exists(alternative):
                return alternative
        raise IOError('File does not exist: {}'.format(fname))

    def path(self, fpath):
        if not os.path.isabs(fpath):
            fpath = os.path.join(self.data_folder, fpath)
        return fpath

    def open(self, fpath, mode='r'):
        if 'w' in mode:
            # When writing, only use absolute paths or data_folder
            fpath = self.path(fpath)
        else:
            fpath = self.find_file(fpath)

        return open(fpath, mode=mode)

    def serve(self, debug=True, **kwargs):
        utils.easy(plugin_list=[self, ], plugin_folder=None, debug=debug, **kwargs)


# For backwards compatibility
SenpyPlugin = Plugin


class Analyser(Plugin):
    '''
    A subclass of Plugin that analyses text and provides an annotation.
    '''

    # Deprecated
    def analyse(self, request, activity):
        return super(Analyser, self).process(request, activity)

    # Deprecated
    def analyse_entries(self, entries, activity):
        for i in super(Analyser, self).process_entries(entries, activity):
            yield i

    def process(self, request, activity, **kwargs):
        return self.analyse(request, activity)

    def process_entries(self, entries, activity):
        for i in self.analyse_entries(entries, activity):
            yield i

    def process_entry(self, entry, activity, **kwargs):
        if hasattr(self, 'analyse_entry'):
            for i in self.analyse_entry(entry, activity):
                yield i
        else:
            super(Analyser, self).process_entry(entry, activity, **kwargs)


AnalysisPlugin = Analyser


class Transformation(AnalysisPlugin):
    '''Empty'''
    pass


class Conversion(Plugin):
    '''
    A subclass of Plugins that convert between different annotation models.
    e.g. a conversion of emotion models, or normalization of sentiment values.
    '''

    def process(self, response, parameters, plugins=None, **kwargs):
        plugins = plugins or []
        newentries = []
        for entry in response.entries:
            newentries.append(
                self.convert_entry(entry, parameters, plugins))
        response.entries = newentries
        return response

    def convert_entry(self, entry, parameters, conversions_applied):
        raise NotImplementedError(
            'You should implement a way to convert each entry, or a custom process method'
        )


ConversionPlugin = Conversion


class Evaluable(Plugin):
    '''
    Common class for plugins that can be evaluated with GSITK.

    They should implement the methods below.
    '''

    def as_pipe(self):
        raise Exception('Implement the as_pipe function')

    def evaluate_func(self, X, activity=None):
        raise Exception('Implement the evaluate_func function')

    def evaluate(self, *args, **kwargs):
        return evaluate([self], *args, **kwargs)


class SentimentPlugin(Analyser, Evaluable, models.SentimentPlugin):
    '''
    Sentiment plugins provide sentiment annotation (using Marl)
    '''
    minPolarityValue = 0
    maxPolarityValue = 1

    _terse_keys = Analyser._terse_keys + ['minPolarityValue', 'maxPolarityValue']

    def test_case(self, case):
        if 'polarity' in case:
            expected = case.get('expected', {})
            s = models.Sentiment(_auto_id=False)
            s.marl__hasPolarity = case['polarity']
            if 'marl:hasOpinion' not in expected:
                expected['marl:hasOpinion'] = []
            expected['marl:hasOpinion'].append(s)
            case['expected'] = expected
        super(SentimentPlugin, self).test_case(case)

    def normalize(self, value, minValue, maxValue):
        nv = minValue + (value - self.minPolarityValue) * (
            self.maxPolarityValue - self.minPolarityValue) / (maxValue - minValue)
        return nv

    def as_pipe(self):
        pipe = gsitk_compat.Pipeline([('senpy-plugin', ScikitWrapper(self))])
        pipe.name = self.id
        return pipe

    def evaluate_func(self, X, activity=None):
        if activity is None:
            parameters = api.parse_params({},
                                          self.extra_params)
            activity = self.activity(parameters)
        entries = []
        for feat in X:
            if isinstance(feat, list):
                feat = ' '.join(feat)
            entries.append(models.Entry(nif__isString=feat))
        labels = []
        for e in self.process_entries(entries, activity):
            sent = e.sentiments[0].polarity
            label = -1
            if sent == 'marl:Positive':
                label = 1
            elif sent == 'marl:Negative':
                label = -1
            labels.append(label)
        return labels


class EmotionPlugin(Analyser, models.EmotionPlugin):
    '''
    Emotion plugins provide emotion annotation (using Onyx)
    '''
    minEmotionValue = 0
    maxEmotionValue = 1

    _terse_keys = Analyser._terse_keys + ['minEmotionValue', 'maxEmotionValue']


class EmotionConversion(Conversion):
    '''
    A subclass of Conversion that converts emotion annotations using different models
    '''

    def can_convert(self, fromModel, toModel):
        '''
        Whether this plugin can convert from fromModel to toModel.
        If fromModel is None, it is interpreted as "any Model"
        '''
        for pair in self.onyx__doesConversion:
            if (pair['onyx:conversionTo'] == toModel) and \
               ((fromModel is None) or (pair['onyx:conversionFrom'] == fromModel)):
                return True
        return False


EmotionConversionPlugin = EmotionConversion


class PostProcessing(Plugin):
    '''
    A plugin that converts the output of other plugins (post-processing).
    '''
    def check(self, request, plugins):
        '''Should this plugin be run for this request?'''
        return False


class Box(Analyser):
    '''
    Black box plugins delegate analysis to a function.
    The flow is like this:

    .. code-block::

                   entries --> to_features() --> predict_many() --> to_entry() --> entries'


    In other words: their ``to_features`` method converts a query (entry and a set of parameters)
    into the input to the `predict_one` method, which only uses an array of features.
    The ``to_entry`` method converts the results given by the box into an entry that senpy can
    handle.
    '''

    def to_features(self, entry, activity=None):
        '''Transforms a query (entry+param) into an input for the black box'''
        return entry

    def to_entry(self, features, entry=None, activity=None):
        '''Transforms the results of the black box into an entry'''
        return entry

    def predict_one(self, features, activity=None):
        raise NotImplementedError(
            'You should define the behavior of this plugin')

    def predict_many(self, features, activity=None):
        results = []
        for feat in features:
            results.append(self.predict_one(features=feat, activity=activity))
        return results

    def process_entry(self, entry, activity):
        for i in self.process_entries([entry], activity):
            yield i

    def process_entries(self, entries, activity):
        features = []
        for entry in entries:
            features.append(self.to_features(entry=entry, activity=activity))
        results = self.predict_many(features=features, activity=activity)

        for (result, entry) in zip(results, entries):
            yield self.to_entry(features=result, entry=entry, activity=activity)


class TextBox(Box):
    '''A black box plugin that takes only text as input'''

    def to_features(self, entry, activity):
        return [entry['nif:isString']]


class SentimentBox(TextBox, SentimentPlugin):
    '''
    A box plugin where the output is only a polarity label or a tuple (polarity, polarityValue)
    '''

    classes = ['marl:Positive', 'marl:Neutral', 'marl:Negative']
    binary = True

    def to_entry(self, features, entry, activity, **kwargs):

        if len(features) != len(self.classes):
            raise models.Error('The number of features ({}) does not match the classes '
                               '(plugin.classes ({})'.format(len(features), len(self.classes)))

        minValue = activity.param('marl:minPolarityValue', 0)
        maxValue = activity.param('marl:minPolarityValue', 1)
        activity['marl:minPolarityValue'] = minValue
        activity['marl:maxPolarityValue'] = maxValue

        for k, v in zip(self.classes, features):
            s = models.Sentiment()
            if self.binary:
                if not v:  # Carry on if the value is 0
                    continue
                s['marl:hasPolarity'] = k
            else:
                if v is not None:
                    s['marl:hasPolarity'] = k
                    nv = self.normalize(v, minValue, maxValue)
                    s['marl:polarityValue'] = nv
            s.prov(activity)

            entry.sentiments.append(s)

        return entry


class EmotionBox(TextBox, EmotionPlugin):
    '''
    A box plugin where the output is only an a tuple of emotion labels
    '''

    EMOTIONS = []
    with_intensity = True

    def to_entry(self, features, entry, activity, **kwargs):
        s = models.EmotionSet()

        if len(features) != len(self.EMOTIONS):
            raise Exception(('The number of classes in the plugin and the number of features '
                             'do not match'))

        for label, intensity in zip(self.EMOTIONS, features):
            e = models.Emotion(onyx__hasEmotionCategory=label)
            if self.with_intensity:
                e.onyx__hasEmotionIntensity = intensity
            s.onyx__hasEmotion.append(e)
        s.prov(activity)
        entry.emotions.append(s)
        return entry


class MappingMixin(object):
    @property
    def mappings(self):
        return self._mappings

    @mappings.setter
    def mappings(self, value):
        self._mappings = value

    def to_entry(self, features, entry, activity):
        features = list(features)
        for i, feat in enumerate(features):
            features[i] = self.mappings.get(feat,
                                            self.mappings.get('default',
                                                              feat))
        return super(MappingMixin, self).to_entry(features=features,
                                                  entry=entry,
                                                  activity=activity)


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
                    self.log.warning('Corrupted shelf file: {}'.format(
                        self.shelf_file))
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
        self.log.debug('Saving pickle')
        if hasattr(self, '_sh') and self._sh is not None:
            with self.open(self.shelf_file, 'wb') as f:
                pickle.dump(self._sh, f)


def pfilter(plugins, plugin_type=Analyser, **kwargs):
    """ Filter plugins by different criteria """
    if isinstance(plugins, models.Plugins):
        plugins = plugins.plugins
    elif isinstance(plugins, dict):
        plugins = plugins.values()
    logger.debug('#' * 100)
    logger.debug('plugin_type {}'.format(plugin_type))
    if plugin_type:
        if isinstance(plugin_type, PluginMeta):
            plugin_type = plugin_type.__name__
        try:
            plugin_type = plugin_type[0].upper() + plugin_type[1:]
            pclass = globals()[plugin_type]
            logger.debug('Class: {}'.format(pclass))
            candidates = filter(lambda x: isinstance(x, pclass), plugins)
        except KeyError:
            raise models.Error('{} is not a valid type'.format(plugin_type))
    else:
        candidates = plugins

    if 'name' in kwargs:
        kwargs['name'] = kwargs['name'].lower()

    logger.debug(candidates)

    def matches(plug):
        res = all(getattr(plug, k, None) == v for (k, v) in kwargs.items())
        logger.debug("matching {} with {}: {}".format(plug.name, kwargs, res))
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
        logger.info('%s', line.decode())
    for line in iter(process.stderr.readline, b''):
        logger.error('%s', line.decode())


def missing_requirements(reqs):
    queue = []
    pool = multiprocessing.Pool(4)
    for req in reqs:
        res = pool.apply_async(pkg_resources.get_distribution, (req,))
        queue.append((req, res))
    missing = []
    for req, job in queue:
        try:
            job.get(1)
        except Exception:
            missing.append(req)
    return missing


def install_deps(*plugins):
    installed = False
    nltk_resources = set()
    requirements = []
    for info in plugins:
        requirements = info.get('requirements', [])
        if requirements:
            requirements += missing_requirements(requirements)
        nltk_resources |= set(info.get('nltk_resources', []))
    if requirements:
        logger.info('Installing requirements: ' + str(requirements))
        pip_args = [sys.executable, '-m', 'pip', 'install']
        for req in requirements:
            pip_args.append(req)
        process = subprocess.Popen(
            pip_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _log_subprocess_output(process)
        exitcode = process.wait()
        installed = True
        if exitcode != 0:
            raise models.Error(
                "Dependencies not properly installed: {}".format(pip_args))
    installed |= download(list(nltk_resources))
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


def from_path(fpath, install_on_fail=False, **kwargs):
    logger.debug("Loading plugin from {}".format(fpath))
    if fpath.endswith('.py'):
        # We asume root is the dir of the file, and module is the name of the file
        root = os.path.dirname(fpath)
        module = os.path.basename(fpath)[:-3]
        for instance in _from_module_name(module=module, root=root, **kwargs):
            yield instance
    else:
        info = parse_plugin_info(fpath)
        yield from_info(info, install_on_fail=install_on_fail, **kwargs)


def from_folder(folders, loader=from_path, **kwargs):
    plugins = []
    for fpath in find_plugins(folders):
        for plugin in loader(fpath, **kwargs):
            plugins.append(plugin)
    return plugins


def from_info(info, root=None, install_on_fail=True, **kwargs):
    if any(x not in info for x in ('module', )):
        raise ValueError('Plugin info is not valid: {}'.format(info))
    module = info["module"]

    if not root and '_path' in info:
        root = os.path.dirname(info['_path'])

    fun = partial(one_from_module, module, root=root, info=info, **kwargs)
    try:
        return fun()
    except (ImportError, LookupError):
        install_deps(info)
        return fun()


def parse_plugin_info(fpath):
    logger.debug("Parsing plugin info: {}".format(fpath))
    with open(fpath, 'r') as f:
        info = yaml.load(f, Loader=yaml.FullLoader)
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
    instance = next(
        from_module(module=module, root=root, info=info, **kwargs), None)
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


def _from_module_name(module, root, info=None, **kwargs):
    module = load_module(module, root)
    for plugin in _from_loaded_module(
            module=module, root=root, info=info, **kwargs):
        yield plugin


def _from_loaded_module(module, info=None, **kwargs):
    for cls in _classes_in_module(module):
        yield cls(info=info, **kwargs)
    for instance in _instances_in_module(module):
        yield instance


cached_evs = {}


def evaluate(plugins, datasets, **kwargs):
    for plug in plugins:
        if not hasattr(plug, 'as_pipe'):
            raise models.Error('Plugin {} cannot be evaluated'.format(plug.name))

    if not isinstance(datasets, dict):
        datasets = gsitk_compat.prepare(datasets, download=True)

    tuples = list(product(plugins, datasets))
    missing = []
    for (p, d) in tuples:
        if (p.id, d) not in cached_evs:
            pipe = p.as_pipe()
            missing.append(gsitk_compat.EvalPipeline(pipe, d))
    if missing:
        ev = gsitk_compat.Eval(tuples=missing, datasets=datasets)
        ev.evaluate()
        results = ev.results
        new_ev = evaluations_to_JSONLD(results, **kwargs)
        for ev in new_ev:
            dataset = ev.evaluatesOn
            model = ev.evaluates
            cached_evs[(model, dataset)] = ev
    evaluations = []
    logger.debug('%s. Cached evs: %s', tuples, cached_evs)
    for (p, d) in tuples:
        logger.debug('Adding %s, %s', d, p)
        evaluations.append(cached_evs[(p.id, d)])
    return evaluations


def evaluations_to_JSONLD(results, flatten=False):
    '''
    Map the evaluation results to a JSONLD scheme
    '''

    evaluations = list()
    metric_names = ['accuracy', 'precision_macro', 'recall_macro',
                    'f1_macro', 'f1_weighted', 'f1_micro', 'f1_macro']

    for index, row in results.fillna('Not Available').iterrows():
        evaluation = models.Evaluation()
        if row.get('CV', True):
            evaluation['@type'] = ['StaticCV', 'Evaluation']
        evaluation.evaluatesOn = row['Dataset']
        evaluation.evaluates = row['Model'].rstrip('__' + row['Dataset'])
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
                metric['@type'] = name.capitalize()
                metric.value = row[name]
                evaluation.metrics.append(metric)
                i += 1
        evaluations.append(evaluation)
    return evaluations


class ScikitWrapper(BaseEstimator, TransformerMixin):
    def __init__(self, plugin=None):
        self.plugin = plugin

    def fit(self, X=None, y=None):
        if self.plugin is not None and not self.plugin.is_activated:
            self.plugin.activate()
        return self

    def transform(self, X):
        return self.plugin.evaluate_func(X, None)

    def predict(self, X):
        return self.transform(X)

    def fit_transform(self, X, y):
        self.fit(X, y)
        return self.transform(X)
