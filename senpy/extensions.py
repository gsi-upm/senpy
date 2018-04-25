"""
Main class for Senpy.
It orchestrates plugin (de)activation and analysis.
"""
from future import standard_library
standard_library.install_aliases()

from . import plugins, api
from .plugins import Plugin, evaluate
from .models import Error, AggregatedEvaluation
from .blueprints import api_blueprint, demo_blueprint, ns_blueprint

from threading import Thread
from functools import partial
import os
import copy
import errno
import logging


logger = logging.getLogger(__name__)

try:
    from gsitk.datasets.datasets import DatasetManager
    GSITK_AVAILABLE = True
except ImportError:
    logger.warn('GSITK is not installed. Some functions will be unavailable.')
    GSITK_AVAILABLE = False


class Senpy(object):
    """ Default Senpy extension for Flask """
    def __init__(self,
                 app=None,
                 plugin_folder=".",
                 data_folder=None,
                 default_plugins=False):

        default_data = os.path.join(os.getcwd(), 'senpy_data')
        self.data_folder = data_folder or os.environ.get('SENPY_DATA', default_data)
        try:
            os.makedirs(self.data_folder)
        except OSError as e:
            if e.errno == errno.EEXIST:
                logger.debug('Data folder exists: {}'.format(self.data_folder))
            else:  # pragma: no cover
                raise

        self._default = None
        self._plugins = {}
        if plugin_folder:
            self.add_folder(plugin_folder)

        if default_plugins:
            self.add_folder('plugins', from_root=True)
        else:
            # Add only conversion plugins
            self.add_folder(os.path.join('plugins', 'conversion'),
                            from_root=True)
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """ Initialise a flask app to add plugins to its context """
        """
        Note: I'm not particularly fond of adding self.app and app.senpy, but
        I can't think of a better way to do it.
        """
        app.senpy = self
        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:  # pragma: no cover
            app.teardown_request(self.teardown)
        app.register_blueprint(api_blueprint, url_prefix="/api")
        app.register_blueprint(ns_blueprint, url_prefix="/ns")
        app.register_blueprint(demo_blueprint, url_prefix="/")

    def add_plugin(self, plugin):
        self._plugins[plugin.name.lower()] = plugin

    def delete_plugin(self, plugin):
        del self._plugins[plugin.name.lower()]

    def plugins(self, **kwargs):
        """ Return the plugins registered for a given application. Filtered by criteria  """
        return list(plugins.pfilter(self._plugins, **kwargs))

    def get_plugin(self, name, default=None):
        if name == 'default':
            return self.default_plugin
        plugin = name.lower()
        if plugin in self._plugins:
            return self._plugins[plugin]

        results = self.plugins(id='plugins/{}'.format(name))

        if not results:
            return Error(message="Plugin not found", status=404)
        return results[0]

    @property
    def analysis_plugins(self):
        """ Return only the analysis plugins """
        return self.plugins(plugin_type='analysisPlugin')

    def add_folder(self, folder, from_root=False):
        """ Find plugins in this folder and add them to this instance """
        if from_root:
            folder = os.path.join(os.path.dirname(__file__), folder)
        logger.debug("Adding folder: %s", folder)
        if os.path.isdir(folder):
            new_plugins = plugins.from_folder([folder],
                                              data_folder=self.data_folder)
            for plugin in new_plugins:
                self.add_plugin(plugin)
        else:
            raise AttributeError("Not a folder or does not exist: %s", folder)

    def _get_plugins(self, request):
        if not self.analysis_plugins:
            raise Error(
                status=404,
                message=("No plugins found."
                         " Please install one."))
        algos = request.parameters.get('algorithm', None)
        if not algos:
            if self.default_plugin:
                algos = [self.default_plugin.name, ]
            else:
                raise Error(
                    status=404,
                    message="No default plugin found, and None provided")

        plugins = list()
        for algo in algos:
            algo = algo.lower()
            if algo not in self._plugins:
                msg = ("The algorithm '{}' is not valid\n"
                       "Valid algorithms: {}").format(algo,
                                                      self._plugins.keys())
                logger.debug(msg)
                raise Error(
                    status=404,
                    message=msg)
            plugins.append(self._plugins[algo])
        return plugins

    def _process_entries(self, entries, req, plugins):
        """
        Recursively process the entries with the first plugin in the list, and pass the results
        to the rest of the plugins.
        """
        if not plugins:
            for i in entries:
                yield i
            return
        plugin = plugins[0]
        self._activate(plugin)  # Make sure the plugin is activated
        specific_params = api.parse_extra_params(req, plugin)
        req.analysis.append({'plugin': plugin,
                             'parameters': specific_params})
        results = plugin.analyse_entries(entries, specific_params)
        for i in self._process_entries(results, req, plugins[1:]):
            yield i

    def install_deps(self):
        for plugin in self.plugins(is_activated=True):
            plugins.install_deps(plugin)

    def analyse(self, request):
        """
        Main method that analyses a request, either from CLI or HTTP.
        It takes a processed request, provided by the user, as returned
        by api.parse_call().
        """
        logger.debug("analysing request: {}".format(request))
        entries = request.entries
        request.entries = []
        plugins = self._get_plugins(request)
        results = request
        for i in self._process_entries(entries, results, plugins):
            results.entries.append(i)
        self.convert_emotions(results)
        logger.debug("Returning analysis result: {}".format(results))
        results.analysis = [i['plugin'].id for i in results.analysis]
        return results

    def _get_datasets(self, request):
        if not self.datasets:
            raise Error(
                status=404,
                message=("No datasets found."
                         " Please verify DatasetManager"))
        datasets_name = request.parameters.get('dataset', None).split(',')
        for dataset in datasets_name:
            if dataset not in self.datasets:
                logger.debug(("The dataset '{}' is not valid\n"
                              "Valid datasets: {}").format(dataset,
                                                           self.datasets.keys()))
                raise Error(
                    status=404,
                    message="The dataset '{}' is not valid".format(dataset))
        dm = DatasetManager()
        datasets = dm.prepare_datasets(datasets_name)
        return datasets

    @property
    def datasets(self):
        if not GSITK_AVAILABLE:
            raise Exception('GSITK is not available. Install it to use this function.')
        self._dataset_list = {}
        dm = DatasetManager()
        for item in dm.get_datasets():
            for key in item:
                if key in self._dataset_list:
                    continue
                properties = item[key]
                properties['@id'] = key
                self._dataset_list[key] = properties
        return self._dataset_list

    def evaluate(self, params):
        if not GSITK_AVAILABLE:
            raise Exception('GSITK is not available. Install it to use this function.')
        logger.debug("evaluating request: {}".format(params))
        results = AggregatedEvaluation()
        results.parameters = params
        datasets = self._get_datasets(results)
        plugins = self._get_plugins(results)
        for eval in evaluate(plugins, datasets):
            results.evaluations.append(eval)
        if 'with_parameters' not in results.parameters:
            del results.parameters
        logger.debug("Returning evaluation result: {}".format(results))
        return results

    def _conversion_candidates(self, fromModel, toModel):
        candidates = self.plugins(plugin_type='emotionConversionPlugin')
        for candidate in candidates:
            for pair in candidate.onyx__doesConversion:
                logging.debug(pair)

                if pair['onyx:conversionFrom'] == fromModel \
                   and pair['onyx:conversionTo'] == toModel:
                    yield candidate

    def convert_emotions(self, resp):
        """
        Conversion of all emotions in a response **in place**.
        In addition to converting from one model to another, it has
        to include the conversion plugin to the analysis list.
        Needless to say, this is far from an elegant solution, but it works.
        @todo refactor and clean up
        """
        plugins = [i['plugin'] for i in resp.analysis]
        params = resp.parameters
        toModel = params.get('emotionModel', None)
        if not toModel:
            return

        logger.debug('Asked for model: {}'.format(toModel))
        output = params.get('conversion', None)
        candidates = {}
        for plugin in plugins:
            try:
                fromModel = plugin.get('onyx:usesEmotionModel', None)
                candidates[plugin.id] = next(self._conversion_candidates(fromModel, toModel))
                logger.debug('Analysis plugin {} uses model: {}'.format(plugin.id, fromModel))
            except StopIteration:
                e = Error(('No conversion plugin found for: '
                           '{} -> {}'.format(fromModel, toModel)),
                          status=404)
                e.original_response = resp
                e.parameters = params
                raise e
        newentries = []
        for i in resp.entries:
            if output == "full":
                newemotions = copy.deepcopy(i.emotions)
            else:
                newemotions = []
            for j in i.emotions:
                plugname = j['prov:wasGeneratedBy']
                candidate = candidates[plugname]
                resp.analysis.append({'plugin': candidate,
                                      'parameters': params})
                for k in candidate.convert(j, fromModel, toModel, params):
                    k.prov__wasGeneratedBy = candidate.id
                    if output == 'nested':
                        k.prov__wasDerivedFrom = j
                    newemotions.append(k)
            i.emotions = newemotions
            newentries.append(i)
        resp.entries = newentries

    @property
    def default_plugin(self):
        if not self._default or not self._default.is_activated:
            candidates = self.plugins(plugin_type='analysisPlugin',
                                      is_activated=True)
            if len(candidates) > 0:
                self._default = candidates[0]
            else:
                self._default = None
            logger.debug("Default: {}".format(self._default))
        return self._default

    @default_plugin.setter
    def default_plugin(self, value):
        if isinstance(value, Plugin):
            if not value.is_activated:
                raise AttributeError('The default plugin has to be activated.')
            self._default = value

        else:
            self._default = self._plugins[value.lower()]

    def activate_all(self, sync=True):
        ps = []
        for plug in self._plugins.keys():
            ps.append(self.activate_plugin(plug, sync=sync))
        return ps

    def deactivate_all(self, sync=True):
        ps = []
        for plug in self._plugins.keys():
            ps.append(self.deactivate_plugin(plug, sync=sync))
        return ps

    def _set_active(self, plugin, active=True, *args, **kwargs):
        ''' We're using a variable in the plugin itself to activate/deactivate plugins.\
        Note that plugins may activate themselves by setting this variable.
        '''
        plugin.is_activated = active

    def _activate(self, plugin):
        success = False
        with plugin._lock:
            if plugin.is_activated:
                return
            plugin.activate()
            msg = "Plugin activated: {}".format(plugin.name)
            logger.info(msg)
            success = True
            self._set_active(plugin, success)

    def activate_plugin(self, plugin_name, sync=True):
        plugin_name = plugin_name.lower()
        if plugin_name not in self._plugins:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)
        plugin = self._plugins[plugin_name]

        logger.info("Activating plugin: {}".format(plugin.name))

        if sync or 'async' in plugin and not plugin.async:
            self._activate(plugin)
        else:
            th = Thread(target=partial(self._activate, plugin))
            th.start()
            return th

    def _deactivate(self, plugin):
        with plugin._lock:
            if not plugin.is_activated:
                return
            plugin.deactivate()
            logger.info("Plugin deactivated: {}".format(plugin.name))

    def deactivate_plugin(self, plugin_name, sync=True):
        plugin_name = plugin_name.lower()
        if plugin_name not in self._plugins:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)
        plugin = self._plugins[plugin_name]

        self._set_active(plugin, False)

        if sync or 'async' in plugin and not plugin.async:
            self._deactivate(plugin)
        else:
            th = Thread(target=partial(self._deactivate, plugin))
            th.start()
            return th

    def teardown(self, exception):
        pass
