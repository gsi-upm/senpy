"""
Main class for Senpy.
It orchestrates plugin (de)activation and analysis.
"""
from future import standard_library
standard_library.install_aliases()

from . import plugins, api
from .plugins import SenpyPlugin
from .models import Error
from .blueprints import api_blueprint, demo_blueprint, ns_blueprint

from threading import Thread
from functools import partial

import os
import copy
import logging
import traceback

logger = logging.getLogger(__name__)


class Senpy(object):
    """ Default Senpy extension for Flask """

    def __init__(self,
                 app=None,
                 plugin_folder=".",
                 default_plugins=False):
        self.app = app
        self._search_folders = set()
        self._plugin_list = []
        self._outdated = True
        self._default = None

        self.add_folder(plugin_folder)
        if default_plugins:
            self.add_folder('plugins', from_root=True)
        else:
            # Add only conversion plugins
            self.add_folder(os.path.join('plugins', 'conversion'),
                            from_root=True)

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
        else:
            app.teardown_request(self.teardown)
        app.register_blueprint(api_blueprint, url_prefix="/api")
        app.register_blueprint(ns_blueprint, url_prefix="/ns")
        app.register_blueprint(demo_blueprint, url_prefix="/")

    def add_folder(self, folder, from_root=False):
        if from_root:
            folder = os.path.join(os.path.dirname(__file__), folder)
        logger.debug("Adding folder: %s", folder)
        if os.path.isdir(folder):
            self._search_folders.add(folder)
            self._outdated = True
        else:
            logger.debug("Not a folder: %s", folder)

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
            if algo not in self.plugins:
                logger.debug(("The algorithm '{}' is not valid\n"
                              "Valid algorithms: {}").format(algo,
                                                             self.plugins.keys()))
                raise Error(
                    status=404,
                    message="The algorithm '{}' is not valid".format(algo))
            plugins.append(self.plugins[algo])
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
        specific_params = api.get_extra_params(req, plugin)
        req.analysis.append({'plugin': plugin,
                             'parameters': specific_params})
        results = plugin.analyse_entries(entries, specific_params)
        for i in self._process_entries(results, req, plugins[1:]):
            yield i

    def install_deps(self):
        for plugin in self.filter_plugins(is_activated=True):
            plugins.install_deps(plugin)

    def analyse(self, request):
        """
        Main method that analyses a request, either from CLI or HTTP.
        It takes a processed request, provided by the user, as returned
        by api.parse_call().
        """
        logger.debug("analysing request: {}".format(request))
        try:
            entries = request.entries
            request.entries = []
            plugins = self._get_plugins(request)
            results = request
            for i in self._process_entries(entries, results, plugins):
                results.entries.append(i)
            self.convert_emotions(results)
            if 'with_parameters' not in results.parameters:
                del results.parameters
            logger.debug("Returning analysis result: {}".format(results))
        except (Error, Exception) as ex:
            if not isinstance(ex, Error):
                msg = "Error during analysis: {} \n\t{}".format(ex,
                                                                traceback.format_exc())
                ex = Error(message=msg, status=500)
            logger.exception('Error returning analysis result')
            raise ex
        results.analysis = [i['plugin'].id for i in results.analysis]
        return results

    def _conversion_candidates(self, fromModel, toModel):
        candidates = self.filter_plugins(plugin_type='emotionConversionPlugin')
        for name, candidate in candidates.items():
            for pair in candidate.onyx__doesConversion:
                logging.debug(pair)

                if pair['onyx:conversionFrom'] == fromModel \
                   and pair['onyx:conversionTo'] == toModel:
                    # logging.debug('Found candidate: {}'.format(candidate))
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
                           '{} -> {}'.format(fromModel, toModel)))
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
        candidate = self._default
        if not candidate:
            candidates = self.filter_plugins(plugin_type='analysisPlugin',
                                             is_activated=True)
            if len(candidates) > 0:
                candidate = list(candidates.values())[0]
        logger.debug("Default: {}".format(candidate))
        return candidate

    @default_plugin.setter
    def default_plugin(self, value):
        if isinstance(value, SenpyPlugin):
            self._default = value
        else:
            self._default = self.plugins[value]

    def activate_all(self, sync=True):
        ps = []
        for plug in self.plugins.keys():
            ps.append(self.activate_plugin(plug, sync=sync))
        return ps

    def deactivate_all(self, sync=True):
        ps = []
        for plug in self.plugins.keys():
            ps.append(self.deactivate_plugin(plug, sync=sync))
        return ps

    def _set_active(self, plugin, active=True, *args, **kwargs):
        ''' We're using a variable in the plugin itself to activate/deactive plugins.\
        Note that plugins may activate themselves by setting this variable.
        '''
        plugin.is_activated = active

    def _activate(self, plugin):
        success = False
        with plugin._lock:
            if plugin.is_activated:
                return
            try:
                plugin.activate()
                msg = "Plugin activated: {}".format(plugin.name)
                logger.info(msg)
                success = True
                self._set_active(plugin, success)
            except Exception as ex:
                msg = "Error activating plugin {} - {} : \n\t{}".format(
                    plugin.name, ex, traceback.format_exc())
                logger.error(msg)
                raise Error(msg)

    def activate_plugin(self, plugin_name, sync=True):
        try:
            plugin = self.plugins[plugin_name]
        except KeyError:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)

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
            try:
                plugin.deactivate()
                logger.info("Plugin deactivated: {}".format(plugin.name))
            except Exception as ex:
                logger.error(
                    "Error deactivating plugin {}: {}".format(plugin.name, ex))
                logger.error("Trace: {}".format(traceback.format_exc()))

    def deactivate_plugin(self, plugin_name, sync=True):
        try:
            plugin = self.plugins[plugin_name]
        except KeyError:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)

        self._set_active(plugin, False)

        if sync or 'async' in plugin and not plugin.async:
            self._deactivate(plugin)
        else:
            th = Thread(target=partial(self._deactivate, plugin))
            th.start()
            return th

    def teardown(self, exception):
        pass

    @property
    def plugins(self):
        """ Return the plugins registered for a given application.  """
        if self._outdated:
            self._plugin_list = plugins.load_plugins(self._search_folders)
            self._outdated = False
        return self._plugin_list

    def filter_plugins(self, **kwargs):
        return plugins.pfilter(self.plugins, **kwargs)

    @property
    def analysis_plugins(self):
        """ Return only the analysis plugins """
        return self.filter_plugins(plugin_type='analysisPlugin')
