"""
Main class for Senpy.
It orchestrates plugin (de)activation and analysis.
"""
from future import standard_library
standard_library.install_aliases()

from . import plugins, api
from .models import Error, AggregatedEvaluation
from .blueprints import api_blueprint, demo_blueprint, ns_blueprint

from threading import Thread
from functools import partial
import os
import copy
import errno
import logging

from . import gsitk_compat

logger = logging.getLogger(__name__)


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
            self.add_folder(os.path.join('plugins', 'postprocessing'),
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

    def plugins(self, plugin_type=None, is_activated=True, **kwargs):
        """ Return the plugins registered for a given application. Filtered by criteria  """
        return list(plugins.pfilter(self._plugins, plugin_type=plugin_type,
                                    is_activated=is_activated, **kwargs))

    def get_plugin(self, name, default=None):
        if name == 'default':
            return self.default_plugin
        elif name == 'conversion':
            return None

        if name.lower() in self._plugins:
            return self._plugins[name.lower()]

        results = self.plugins(id='endpoint:plugins/{}'.format(name.lower()),
                               plugin_type=None)
        if results:
            return results[0]

        results = self.plugins(id=name,
                               plugin_type=None)
        if results:
            return results[0]

        msg = ("Plugin not found: '{}'\n"
               "Make sure it is ACTIVATED\n"
                "Valid algorithms: {}").format(name,
                                              self._plugins.keys())
        raise Error(message=msg, status=404)

    def get_plugins(self, name):
        try:
            name = name.split(',')
        except AttributeError:
            pass  # Assume it is a tuple or a list
        return tuple(self.get_plugin(n) for n in name)

    @property
    def analysis_plugins(self):
        """ Return only the analysis plugins that are active"""
        return self.plugins(plugin_type='analysisPlugin', is_activated=True)

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

    # def check_analysis_request(self, analysis):
    #     '''Check if the analysis request can be fulfilled'''
    #     if not self.plugins():
    #         raise Error(
    #             status=404,
    #             message=("No plugins found."
    #                      " Please install one."))
    #     for a in analysis:
    #         algo = a.algorithm
    #         if algo == 'default' and not self.default_plugin:
    #             raise Error(
    #                 status=404,
    #                 message="No default plugin found, and None provided")
    #         else:
    #             self.get_plugin(algo)


    def _process(self, req, pending, done=None):
        """
        Recursively process the entries with the first plugin in the list, and pass the results
        to the rest of the plugins.
        """
        done = done or []
        if not pending:
            return req

        analysis = pending[0]
        results = analysis.run(req)
        results.analysis.append(analysis)
        done += analysis
        return self._process(results, pending[1:], done)

    def install_deps(self):
        plugins.install_deps(*self.plugins())

    def analyse(self, request, analysis=None):
        """
        Main method that analyses a request, either from CLI or HTTP.
        It takes a processed request, provided by the user, as returned
        by api.parse_call().
        """
        if not self.plugins():
            raise Error(
                status=404,
                message=("No plugins found."
                         " Please install one."))
        if analysis is None:
            params = str(request)
            plugins = self.get_plugins(request.parameters['algorithm'])
            analysis = api.parse_analysis(request.parameters, plugins)
        logger.debug("analysing request: {}".format(request))
        results = self._process(request, analysis)
        logger.debug("Got analysis result: {}".format(results))
        results = self.postprocess(results)
        logger.debug("Returning post-processed result: {}".format(results))
        return results

    def convert_emotions(self, resp):
        """
        Conversion of all emotions in a response **in place**.
        In addition to converting from one model to another, it has
        to include the conversion plugin to the analysis list.
        Needless to say, this is far from an elegant solution, but it works.
        @todo refactor and clean up
        """
        plugins = resp.analysis

        if 'parameters' not in resp:
            return resp

        params = resp['parameters']
        toModel = params.get('emotionModel', None)
        if not toModel:
            return resp

        logger.debug('Asked for model: {}'.format(toModel))
        output = params.get('conversion', None)
        candidates = {}
        for plugin in plugins:
            try:
                fromModel = plugin.get('onyx:usesEmotionModel', None)
                candidates[plugin.id] = next(self._conversion_candidates(fromModel, toModel))
                logger.debug('Analysis plugin {} uses model: {}'.format(
                    plugin.id, fromModel))
            except StopIteration:
                e = Error(('No conversion plugin found for: '
                           '{} -> {}'.format(fromModel, toModel)),
                          status=404)
                e.original_response = resp
                e.parameters = params
                raise e
        newentries = []
        done = []
        for i in resp.entries:
            if output == "full":
                newemotions = copy.deepcopy(i.emotions)
            else:
                newemotions = []
            for j in i.emotions:
                plugname = j['prov:wasGeneratedBy']
                candidate = candidates[plugname]
                done.append({'plugin': candidate, 'parameters': params})
                for k in candidate.convert(j, fromModel, toModel, params):
                    k.prov__wasGeneratedBy = candidate.id
                    if output == 'nested':
                        k.prov__wasDerivedFrom = j
                    newemotions.append(k)
            i.emotions = newemotions
            newentries.append(i)
        resp.entries = newentries
        return resp

    def _conversion_candidates(self, fromModel, toModel):
        candidates = self.plugins(plugin_type=plugins.EmotionConversion)
        for candidate in candidates:
            for pair in candidate.onyx__doesConversion:
                logging.debug(pair)
                if candidate.can_convert(fromModel, toModel):
                    yield candidate

    def postprocess(self, response):
        '''
        Transform the results from the analysis plugins.
        It has some pre-defined post-processing like emotion conversion,
        and it also allows plugins to auto-select themselves.
        '''

        response = self.convert_emotions(response)

        for plug in self.plugins(plugin_type=plugins.PostProcessing):
            if plug.check(response, response.analysis):
                response = plug.process(response)
        return response

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
                              "Valid datasets: {}").format(
                                  dataset, self.datasets.keys()))
                raise Error(
                    status=404,
                    message="The dataset '{}' is not valid".format(dataset))
        dm = gsitk_compat.DatasetManager()
        datasets = dm.prepare_datasets(datasets_name)
        return datasets

    @property
    def datasets(self):
        self._dataset_list = {}
        dm = gsitk_compat.DatasetManager()
        for item in dm.get_datasets():
            for key in item:
                if key in self._dataset_list:
                    continue
                properties = item[key]
                properties['@id'] = key
                self._dataset_list[key] = properties
        return self._dataset_list

    def evaluate(self, params):
        logger.debug("evaluating request: {}".format(params))
        results = AggregatedEvaluation()
        results.parameters = params
        datasets = self._get_datasets(results)
        plugins = []
        for plugname in params.algorithm:
            plugins = self.get_plugin(plugname)

        for eval in plugins.evaluate(plugins, datasets):
            results.evaluations.append(eval)
        if 'with_parameters' not in results.parameters:
            del results.parameters
        logger.debug("Returning evaluation result: {}".format(results))
        return results

    @property
    def default_plugin(self):
        if not self._default or not self._default.is_activated:
            candidates = self.plugins(
                plugin_type='analysisPlugin', is_activated=True)
            if len(candidates) > 0:
                self._default = candidates[0]
            else:
                self._default = None
            logger.debug("Default: {}".format(self._default))
        return self._default

    @default_plugin.setter
    def default_plugin(self, value):
        if isinstance(value, plugins.Plugin):
            if not value.is_activated:
                raise AttributeError('The default plugin has to be activated.')
            self._default = value

        else:
            self._default = self._plugins[value.lower()]

    def activate_all(self, sync=True, allow_fail=False):
        ps = []
        for plug in self._plugins.keys():
            try:
                self.activate_plugin(plug, sync=sync)
            except Exception as ex:
                if not allow_fail:
                    raise
                logger.error('Could not activate {}: {}'.format(plug, ex))
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
        return success

    def activate_plugin(self, plugin_name, sync=True):
        plugin_name = plugin_name.lower()
        if plugin_name not in self._plugins:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)
        plugin = self._plugins[plugin_name]

        logger.info("Activating plugin: {}".format(plugin.name))

        if sync or not getattr(plugin, 'async', True) or getattr(
                plugin, 'sync', False):
            return self._activate(plugin)
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

        if sync or not getattr(plugin, 'async', True) or not getattr(
                plugin, 'sync', False):
            self._deactivate(plugin)
        else:
            th = Thread(target=partial(self._deactivate, plugin))
            th.start()
            return th

    def teardown(self, exception):
        pass
