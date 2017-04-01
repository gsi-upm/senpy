"""
Main class for Senpy.
It orchestrates plugin (de)activation and analysis.
"""
from future import standard_library
standard_library.install_aliases()

from . import plugins
from .plugins import SenpyPlugin
from .models import Error, Entry, Results, from_dict
from .blueprints import api_blueprint, demo_blueprint, ns_blueprint
from .api import API_PARAMS, NIF_PARAMS, parse_params

from threading import Thread

import os
import copy
import fnmatch
import inspect
import sys
import importlib
import logging
import traceback
import yaml
import pip

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

    def _find_plugins(self, params):
        if not self.analysis_plugins:
            raise Error(
                status=404,
                message=("No plugins found."
                         " Please install one."))
        api_params = parse_params(params, spec=API_PARAMS)
        algos = None
        if "algorithm" in api_params and api_params["algorithm"]:
            algos = api_params["algorithm"].split(',')
        elif self.default_plugin:
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

            if not self.plugins[algo].is_activated:
                logger.debug("Plugin not activated: {}".format(algo))
                raise Error(
                    status=400,
                    message=("The algorithm '{}'"
                             " is not activated yet").format(algo))
            plugins.append(self.plugins[algo])
        return plugins

    def _get_params(self, params, plugin=None):
        nif_params = parse_params(params, spec=NIF_PARAMS)
        if plugin:
            extra_params = plugin.get('extra_params', {})
            specific_params = parse_params(params, spec=extra_params)
            nif_params.update(specific_params)
        return nif_params

    def _get_entries(self, params):
        if params['informat'] == 'text':
            results = Results()
            entry = Entry(text=params['input'])
            results.entries.append(entry)
        elif params['informat'] == 'json-ld':
            results = from_dict(params['input'])
        else:
            raise NotImplemented('Informat {} is not implemented'.format(params['informat']))
        return results

    def _process_entries(self, entries, plugins, nif_params):
        if not plugins:
            for i in entries:
                yield i
            return
        plugin = plugins[0]
        specific_params = self._get_params(nif_params, plugin)
        results = plugin.analyse_entries(entries, specific_params)
        for i in self._process_entries(results, plugins[1:], nif_params):
            yield i

    def _process_response(self, resp, plugins, nif_params):
        entries = resp.entries
        resp.entries = []
        for plug in plugins:
            resp.analysis.append(plug.id)
        for i in self._process_entries(entries, plugins, nif_params):
            resp.entries.append(i)
        return resp

    def analyse(self, **api_params):
        """
        Main method that analyses a request, either from CLI or HTTP.
        It uses a dictionary of parameters, provided by the user.
        """
        logger.debug("analysing with params: {}".format(api_params))
        plugins = self._find_plugins(api_params)
        nif_params = self._get_params(api_params)
        resp = self._get_entries(nif_params)
        if 'with_parameters' in api_params:
            resp.parameters = nif_params
        try:
            resp = self._process_response(resp, plugins, nif_params)
            self.convert_emotions(resp, plugins, nif_params)
            logger.debug("Returning analysis result: {}".format(resp))
        except (Error, Exception) as ex:
            if not isinstance(ex, Error):
                ex = Error(message=str(ex), status=500)
            logger.exception('Error returning analysis result')
            raise ex
        return resp

    def _conversion_candidates(self, fromModel, toModel):
        candidates = self.filter_plugins(**{'@type': 'emotionConversionPlugin'})
        for name, candidate in candidates.items():
            for pair in candidate.onyx__doesConversion:
                logging.debug(pair)

                if pair['onyx:conversionFrom'] == fromModel \
                   and pair['onyx:conversionTo'] == toModel:
                    # logging.debug('Found candidate: {}'.format(candidate))
                    yield candidate

    def convert_emotions(self, resp, plugins, params):
        """
        Conversion of all emotions in a response.
        In addition to converting from one model to another, it has
        to include the conversion plugin to the analysis list.
        Needless to say, this is far from an elegant solution, but it works.
        @todo refactor and clean up
        """
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
        resp.analysis = set(resp.analysis)
        for i in resp.entries:
            if output == "full":
                newemotions = copy.deepcopy(i.emotions)
            else:
                newemotions = []
            for j in i.emotions:
                plugname = j['prov:wasGeneratedBy']
                candidate = candidates[plugname]
                resp.analysis.add(candidate.id)
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
            candidates = self.filter_plugins(is_activated=True)
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

    def activate_all(self, sync=False):
        ps = []
        for plug in self.plugins.keys():
            ps.append(self.activate_plugin(plug, sync=sync))
        return ps

    def deactivate_all(self, sync=False):
        ps = []
        for plug in self.plugins.keys():
            ps.append(self.deactivate_plugin(plug, sync=sync))
        return ps

    def _set_active_plugin(self, plugin_name, active=True, *args, **kwargs):
        ''' We're using a variable in the plugin itself to activate/deactive plugins.\
        Note that plugins may activate themselves by setting this variable.
        '''
        self.plugins[plugin_name].is_activated = active

    def activate_plugin(self, plugin_name, sync=False):
        try:
            plugin = self.plugins[plugin_name]
        except KeyError:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)

        logger.info("Activating plugin: {}".format(plugin.name))

        def act():
            success = False
            try:
                plugin.activate()
                msg = "Plugin activated: {}".format(plugin.name)
                logger.info(msg)
                success = True
                self._set_active_plugin(plugin_name, success)
            except Exception as ex:
                msg = "Error activating plugin {} - {} : \n\t{}".format(
                    plugin.name, ex, traceback.format_exc())
                logger.error(msg)
                raise Error(msg)

        if sync or 'async' in plugin and not plugin.async:
            act()
        else:
            th = Thread(target=act)
            th.start()

    def deactivate_plugin(self, plugin_name, sync=False):
        try:
            plugin = self.plugins[plugin_name]
        except KeyError:
            raise Error(
                message="Plugin not found: {}".format(plugin_name), status=404)

        self._set_active_plugin(plugin_name, False)

        def deact():
            try:
                plugin.deactivate()
                logger.info("Plugin deactivated: {}".format(plugin.name))
            except Exception as ex:
                logger.error(
                    "Error deactivating plugin {}: {}".format(plugin.name, ex))
                logger.error("Trace: {}".format(traceback.format_exc()))

        if sync or 'async' in plugin and not plugin.async:
            deact()
        else:
            th = Thread(target=deact)
            th.start()

    @classmethod
    def validate_info(cls, info):
        return all(x in info for x in ('name', 'module', 'description', 'version'))

    def install_deps(self):
        for i in self.plugins.values():
            self._install_deps(i)

    @classmethod
    def _install_deps(cls, info=None):
        requirements = info.get('requirements', [])
        if requirements:
            pip_args = []
            pip_args.append('install')
            pip_args.append('--use-wheel')
            for req in requirements:
                pip_args.append(req)
            logger.info('Installing requirements: ' + str(requirements))

            cmd_name, cmd_args = pip.parseopts(pip_args)
            command = pip.commands_dict[cmd_name](isolated=pip.check_isolated(cmd_args))
            options, args = command.parse_args(cmd_args)
            command.run(options, args)

    @classmethod
    def _load_module(cls, name, root):
        sys.path.append(root)
        tmp = importlib.import_module(name)
        sys.path.remove(root)
        return tmp

    @classmethod
    def _load_plugin_from_info(cls, info, root):
        if not cls.validate_info(info):
            logger.warn('The module info is not valid.\n\t{}'.format(info))
            return None, None
        module = info["module"]
        name = info["name"]

        cls._install_deps(info)
        tmp = cls._load_module(module, root)

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
        module = candidate(info=info)
        return name, module

    @classmethod
    def _load_plugin(cls, root, filename):
        fpath = os.path.join(root, filename)
        logger.debug("Loading plugin: {}".format(fpath))
        with open(fpath, 'r') as f:
            info = yaml.load(f)
        logger.debug("Info: {}".format(info))
        return cls._load_plugin_from_info(info, root)

    def _load_plugins(self):
        plugins = {}
        for search_folder in self._search_folders:
            for root, dirnames, filenames in os.walk(search_folder):
                for filename in fnmatch.filter(filenames, '*.senpy'):
                    name, plugin = self._load_plugin(root, filename)
                    if plugin and name:
                        plugins[name] = plugin

        self._outdated = False
        return plugins

    def teardown(self, exception):
        pass

    @property
    def plugins(self):
        """ Return the plugins registered for a given application.  """
        if self._outdated:
            self._plugin_list = self._load_plugins()
        return self._plugin_list

    def filter_plugins(self, **kwargs):
        """ Filter plugins by different criteria """
        ptype = kwargs.pop('plugin_type', None)
        logger.debug('#' * 100)
        logger.debug('ptype {}'.format(ptype))
        if ptype:
            try:
                ptype = ptype[0].upper() + ptype[1:]
                pclass = getattr(plugins, ptype)
                logger.debug('Class: {}'.format(pclass))
                candidates = filter(lambda x: isinstance(x, pclass),
                                    self.plugins.values())
            except AttributeError:
                raise Error('{} is not a valid type'.format(ptype))
        else:
            candidates = self.plugins.values()

        logger.debug(candidates)

        def matches(plug):
            res = all(getattr(plug, k, None) == v for (k, v) in kwargs.items())
            logger.debug(
                "matching {} with {}: {}".format(plug.name, kwargs, res))
            return res

        if kwargs:
            candidates = filter(matches, candidates)
        return {p.name: p for p in candidates}

    @property
    def analysis_plugins(self):
        """ Return only the analysis plugins """
        return self.filter_plugins(plugin_type='analysisPlugin')
