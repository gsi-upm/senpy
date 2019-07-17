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
"""
Main class for Senpy.
It orchestrates plugin (de)activation and analysis.
"""
from future import standard_library
standard_library.install_aliases()

from . import plugins, api
from .models import Error, AggregatedEvaluation
from .plugins import AnalysisPlugin
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
        self._conversion_candidates = {}

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
        self._conversion_candidates = {}

    def delete_plugin(self, plugin):
        del self._plugins[plugin.name.lower()]

    def plugins(self, plugin_type=None, is_activated=True, **kwargs):
        """ Return the plugins registered for a given application. Filtered by criteria  """
        return sorted(plugins.pfilter(self._plugins,
                                      plugin_type=plugin_type,
                                      is_activated=is_activated,
                                      **kwargs),
                      key=lambda x: x.id)

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

    def analysis_plugins(self, **kwargs):
        """ Return only the analysis plugins that are active"""
        candidates = self.plugins(**kwargs)
        return list(plugins.pfilter(candidates, plugin_type=AnalysisPlugin))

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
        results.activities.append(analysis)
        done += analysis
        return self._process(results, pending[1:], done)

    def install_deps(self):
        logger.info('Installing dependencies')
        # If a plugin is activated, its dependencies should already be installed
        # Otherwise, it would've failed to activate.
        plugins.install_deps(*self.plugins(is_activated=False))

    def analyse(self, request, analyses=None):
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
        if analyses is None:
            plugins = self.get_plugins(request.parameters['algorithm'])
            analyses = api.parse_analyses(request.parameters, plugins)
        logger.debug("analysing request: {}".format(request))
        results = self._process(request, analyses)
        logger.debug("Got analysis result: {}".format(results))
        results = self.postprocess(results, analyses)
        logger.debug("Returning post-processed result: {}".format(results))
        return results

    def convert_emotions(self, resp, analyses):
        """
        Conversion of all emotions in a response **in place**.
        In addition to converting from one model to another, it has
        to include the conversion plugin to the analysis list.
        Needless to say, this is far from an elegant solution, but it works.
        @todo refactor and clean up
        """

        logger.debug("Converting emotions")
        if 'parameters' not in resp:
            logger.debug("NO PARAMETERS")
            return resp

        params = resp['parameters']
        toModel = params.get('emotion-model', None)
        if not toModel:
            logger.debug("NO tomodel PARAMETER")
            return resp

        logger.debug('Asked for model: {}'.format(toModel))
        output = params.get('conversion', None)

        newentries = []
        done = []
        for i in resp.entries:

            if output == "full":
                newemotions = copy.deepcopy(i.emotions)
            else:
                newemotions = []
            for j in i.emotions:
                activity = j['prov:wasGeneratedBy']
                act = resp.activity(activity)
                if not act:
                    raise Error('Could not find the emotion model for {}'.format(activity))
                fromModel = act.plugin['onyx:usesEmotionModel']
                if toModel == fromModel:
                    continue
                candidate = self._conversion_candidate(fromModel, toModel)
                if not candidate:
                    e = Error(('No conversion plugin found for: '
                              '{} -> {}'.format(fromModel, toModel)),
                              status=404)
                    e.original_response = resp
                    e.parameters = params
                    raise e

                analysis = candidate.activity(params)
                done.append(analysis)
                for k in candidate.convert(j, fromModel, toModel, params):
                    k.prov__wasGeneratedBy = analysis.id
                    if output == 'nested':
                        k.prov__wasDerivedFrom = j
                    newemotions.append(k)
            i.emotions = newemotions
            newentries.append(i)
        resp.entries = newentries
        return resp

    def _conversion_candidate(self, fromModel, toModel):
        if not self._conversion_candidates:
            candidates = {}
            for conv in self.plugins(plugin_type=plugins.EmotionConversion):
                for pair in conv.onyx__doesConversion:
                    logging.debug(pair)
                    key = (pair['onyx:conversionFrom'], pair['onyx:conversionTo'])
                    if key not in candidates:
                        candidates[key] = []
                    candidates[key].append(conv)
            self._conversion_candidates = candidates

        key = (fromModel, toModel)
        if key not in self._conversion_candidates:
            return None
        return self._conversion_candidates[key][0]

    def postprocess(self, response, analyses):
        '''
        Transform the results from the analysis plugins.
        It has some pre-defined post-processing like emotion conversion,
        and it also allows plugins to auto-select themselves.
        '''

        response = self.convert_emotions(response, analyses)

        for plug in self.plugins(plugin_type=plugins.PostProcessing):
            if plug.check(response, response.activities):
                activity = plug.activity(response.parameters)
                response = plug.process(response, activity)
        return response

    def _get_datasets(self, request):
        datasets_name = request.parameters.get('dataset', None).split(',')
        for dataset in datasets_name:
            if dataset not in gsitk_compat.datasets:
                logger.debug(("The dataset '{}' is not valid\n"
                              "Valid datasets: {}").format(
                                  dataset, gsitk_compat.datasets.keys()))
                raise Error(
                    status=404,
                    message="The dataset '{}' is not valid".format(dataset))
        return datasets_name

    def evaluate(self, params):
        logger.debug("evaluating request: {}".format(params))
        results = AggregatedEvaluation()
        results.parameters = params
        datasets = self._get_datasets(results)
        plugs = []
        for plugname in params['algorithm']:
            plugs = self.get_plugins(plugname)
        for plug in plugs:
            if not isinstance(plug, plugins.Evaluable):
                raise Exception('Plugin {} can not be evaluated', plug.id)

        for eval in plugins.evaluate(plugs, datasets):
            results.evaluations.append(eval)
        if 'with-parameters' not in results.parameters:
            del results.parameters
        logger.debug("Returning evaluation result: {}".format(results))
        return results

    @property
    def default_plugin(self):
        if not self._default or not self._default.is_activated:
            candidates = self.analysis_plugins()
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

    def _activate(self, plugin):
        success = False
        with plugin._lock:
            if plugin.is_activated:
                return
            plugin._activate()
            msg = "Plugin activated: {}".format(plugin.name)
            logger.info(msg)
            success = plugin.is_activated
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
            plugin._deactivate()
            logger.info("Plugin deactivated: {}".format(plugin.name))

    def deactivate_plugin(self, plugin_name, sync=True):
        plugin_name = plugin_name.lower()
        if plugin_name not in self._plugins:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)
        plugin = self._plugins[plugin_name]

        if sync or not getattr(plugin, 'async', True) or not getattr(
                plugin, 'sync', False):
            plugin._deactivate()
        else:
            th = Thread(target=plugin.deactivate)
            th.start()
            return th

    def teardown(self, exception):
        pass
