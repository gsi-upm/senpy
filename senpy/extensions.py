"""
"""
from future import standard_library
standard_library.install_aliases()

from .plugins import SentimentPlugin
from .models import Error
from .blueprints import api_blueprint, demo_blueprint
from .api import API_PARAMS, NIF_PARAMS, parse_params

from git import Repo, InvalidGitRepositoryError

from threading import Thread

import os
import fnmatch
import inspect
import sys
import imp
import logging
import traceback
import yaml
import pip

logger = logging.getLogger(__name__)


class Senpy(object):
    """ Default Senpy extension for Flask """

    def __init__(self,
                 app=None,
                 plugin_folder="plugins",
                 default_plugins=False):
        self.app = app

        self._search_folders = set()
        self._plugin_list = []
        self._outdated = True

        self.add_folder(plugin_folder)
        if default_plugins:
            base_folder = os.path.join(os.path.dirname(__file__), "plugins")
            self.add_folder(base_folder)

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
        app.register_blueprint(demo_blueprint, url_prefix="/")

    def add_folder(self, folder):
        logger.debug("Adding folder: %s", folder)
        if os.path.isdir(folder):
            self._search_folders.add(folder)
            self._outdated = True
        else:
            logger.debug("Not a folder: %s", folder)

    def analyse(self, **params):
        algo = None
        logger.debug("analysing with params: {}".format(params))
        api_params = parse_params(params, spec=API_PARAMS)
        if "algorithm" in api_params and api_params["algorithm"]:
            algo = api_params["algorithm"]
        elif self.plugins:
            algo = self.default_plugin and self.default_plugin.name
        if not algo:
            raise Error(
                status=404,
                message=("No plugins found."
                         " Please install one.").format(algo))
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
        plug = self.plugins[algo]
        nif_params = parse_params(params, spec=NIF_PARAMS)
        extra_params = plug.get('extra_params', {})
        specific_params = parse_params(params, spec=extra_params)
        nif_params.update(specific_params)
        try:
            resp = plug.analyse(**nif_params)
            resp.analysis.append(plug)
            logger.debug("Returning analysis result: {}".format(resp))
        except Exception as ex:
            resp = Error(message=str(ex), status=500)
        return resp

    @property
    def default_plugin(self):
        candidates = self.filter_plugins(is_activated=True)
        if len(candidates) > 0:
            candidate = list(candidates.values())[0]
            logger.debug("Default: {}".format(candidate.name))
            return candidate
        else:
            return None

    def parameters(self, algo):
        return getattr(
            self.plugins.get(algo) or self.default_plugin, "extra_params", {})

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
                    plugin.name, ex, ex.format_exc())
                logger.error(msg)
                raise Error(msg)
        if sync:
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
                logger.error("Error deactivating plugin {}: {}".format(
                    plugin.name, ex))
                logger.error("Trace: {}".format(traceback.format_exc()))

        if sync:
            deact()
        else:
            th = Thread(target=deact)
            th.start()

    def reload_plugin(self, name):
        logger.debug("Reloading {}".format(name))
        plugin = self.plugins[name]
        try:
            del self.plugins[name]
            nplug = self._load_plugin(plugin.module, plugin.path)
            self.plugins[nplug.name] = nplug
        except Exception as ex:
            logger.error('Error reloading {}: {}'.format(name, ex))
            self.plugins[name] = plugin

    @classmethod
    def validate_info(cls, info):
        return all(x in info for x in ('name', 'module', 'version'))

    def install_deps(self):
        for i in self.plugins.values():
            self._install_deps(i._info)

    @classmethod
    def _install_deps(cls, info=None):
        requirements = info.get('requirements', [])
        if requirements:
            pip_args = []
            pip_args.append('install')
            for req in requirements:
                pip_args.append(req)
            logger.info('Installing requirements: ' + str(requirements))
            pip.main(pip_args)

    @classmethod
    def _load_plugin_from_info(cls, info, root):
        if not cls.validate_info(info):
            logger.warn('The module info is not valid.\n\t{}'.format(info))
            return None, None
        module = info["module"]
        name = info["name"]
        sys.path.append(root)
        (fp, pathname, desc) = imp.find_module(module, [root, ])
        try:
            cls._install_deps(info)
            tmp = imp.load_module(module, fp, pathname, desc)
            sys.path.remove(root)
            candidate = None
            for _, obj in inspect.getmembers(tmp):
                if inspect.isclass(obj) and inspect.getmodule(obj) == tmp:
                    logger.debug(("Found plugin class:"
                                  " {}@{}").format(obj, inspect.getmodule(
                                      obj)))
                    candidate = obj
                    break
            if not candidate:
                logger.debug("No valid plugin for: {}".format(module))
                return
            module = candidate(info=info)
            repo_path = root
            module._repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            logger.debug("The plugin {} is not in a Git repository".format(
                module))
            module._repo = None
        except Exception as ex:
            logger.error("Exception importing {}: {}".format(module, ex))
            logger.error("Trace: {}".format(traceback.format_exc()))
            return None, None
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
                    if plugin and name not in self._plugin_list:
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

        def matches(plug):
            res = all(getattr(plug, k, None) == v for (k, v) in kwargs.items())
            logger.debug("matching {} with {}: {}".format(plug.name, kwargs,
                                                          res))
            return res

        if not kwargs:
            return self.plugins
        else:
            return {n: p for n, p in self.plugins.items() if matches(p)}

    def sentiment_plugins(self):
        """ Return only the sentiment plugins """
        return {
            p: plugin
            for p, plugin in self.plugins.items()
            if isinstance(plugin, SentimentPlugin)
        }
