"""
"""
import gevent
from gevent import monkey
monkey.patch_all()

from .plugins import SenpyPlugin, SentimentPlugin, EmotionPlugin
from .models import Error
from .blueprints import nif_blueprint

from git import Repo, InvalidGitRepositoryError
from functools import partial

import os
import fnmatch
import inspect
import sys
import imp
import logging
import gevent
import json

logger = logging.getLogger(__name__)


class Senpy(object):

    """ Default Senpy extension for Flask """

    def __init__(self, app=None, plugin_folder="plugins", default_plugins=False):
        self.app = app

        self._search_folders = set()
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
        app.register_blueprint(nif_blueprint)

    def add_folder(self, folder):
        logger.debug("Adding folder: %s", folder)
        if os.path.isdir(folder):
            self._search_folders.add(folder)
            self._outdated = True
            return True
        else:
            logger.debug("Not a folder: %s", folder)
            return False

    def analyse(self, **params):
        algo = None
        logger.debug("analysing with params: {}".format(params))
        if "algorithm" in params:
            algo = params["algorithm"]
        elif self.plugins:
            algo = self.default_plugin and self.default_plugin.name
        if not algo:
            return Error(status=404,
                         message=("No plugins found."
                                  " Please install one.").format(algo))
        if algo in self.plugins:
            if self.plugins[algo].is_activated:
                plug = self.plugins[algo]
                resp = plug.analyse(**params)
                resp.analysis.append(plug)
                logger.debug("Returning analysis result: {}".format(resp))
                return resp
            else:
                logger.debug("Plugin not activated: {}".format(algo))
                return Error(status=400,
                             message=("The algorithm '{}'"
                                      " is not activated yet").format(algo))
        else:
            logger.debug(("The algorithm '{}' is not valid\n"
                          "Valid algorithms: {}").format(algo,
                                                         self.plugins.keys()))
            return Error(status=404,
                         message="The algorithm '{}' is not valid"
                                 .format(algo))

    @property
    def default_plugin(self):
        candidates = self.filter_plugins(is_activated=True)
        if len(candidates) > 0:
            candidate = candidates.values()[0]
            logger.debug("Default: {}".format(candidate))
            return candidate
        else:
            return None

    def parameters(self, algo):
        return getattr(self.plugins.get(algo) or self.default_plugin,
                       "params",
                       {})

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
        self.plugins[plugin_name].is_activated = active

    def activate_plugin(self, plugin_name, sync=False):
        plugin = self.plugins[plugin_name]
        def act():
            try:
                plugin.activate()
            except Exception as ex:
                logger.error("Error activating plugin {}: {}".format(plugin.name,
                                                                     ex))
        th = gevent.spawn(act)
        th.link_value(partial(self._set_active_plugin, plugin_name, True))
        if sync:
            th.join()
        else:
            return th

    def deactivate_plugin(self, plugin_name, sync=False):
        plugin = self.plugins[plugin_name]
        th = gevent.spawn(plugin.deactivate)
        th.link_value(partial(self._set_active_plugin, plugin_name, False))
        if sync:
            th.join()
        else:
            return th

    def reload_plugin(self, plugin):
        logger.debug("Reloading {}".format(plugin))
        plug = self.plugins[plugin]
        nplug = self._load_plugin(plug.module, plug.path)
        del self.plugins[plugin]
        self.plugins[nplug.name] = nplug

    @staticmethod
    def _load_plugin(root, filename):
        logger.debug("Loading plugin: {}".format(filename))
        fpath = os.path.join(root, filename)
        with open(fpath, 'r') as f:
            info = json.load(f)
        logger.debug("Info: {}".format(info))
        sys.path.append(root)
        module = info["module"]
        name = info["name"]
        (fp, pathname, desc) = imp.find_module(module, [root, ])
        try:
            tmp = imp.load_module(module, fp, pathname, desc)
            sys.path.remove(root)
            candidate = None
            for _, obj in inspect.getmembers(tmp):
                if inspect.isclass(obj) and inspect.getmodule(obj) == tmp:
                    logger.debug(("Found plugin class:"
                                  " {}@{}").format(obj, inspect.getmodule(obj))
                                 )
                    candidate = obj
                    break
            if not candidate:
                logger.debug("No valid plugin for: {}".format(filename))
                return
            module = candidate(info=info)
            try:
                repo_path = root
                module._repo = Repo(repo_path)
            except InvalidGitRepositoryError:
                module._repo = None
        except Exception as ex:
            logger.debug("Exception importing {}: {}".format(filename, ex))
            return None, None
        return name, module

    def _load_plugins(self):
        plugins = {}
        for search_folder in self._search_folders:
            for root, dirnames, filenames in os.walk(search_folder):
                for filename in fnmatch.filter(filenames, '*.senpy'):
                    name, plugin = self._load_plugin(root, filename)
                    if plugin:
                        plugins[name] = plugin

        self._outdated = False
        return plugins

    def teardown(self, exception):
        pass

    @property
    def plugins(self):
        """ Return the plugins registered for a given application.  """
        if not hasattr(self, 'senpy_plugins') or self._outdated:
            self.senpy_plugins = self._load_plugins()
        return self.senpy_plugins

    def filter_plugins(self, **kwargs):
        """ Filter plugins by different criteria """

        def matches(plug):
            res = all(getattr(plug, k, None) == v for (k, v) in kwargs.items())
            logger.debug("matching {} with {}: {}".format(plug.name,
                                                          kwargs,
                                                          res))
            return res

        if not kwargs:
            return self.plugins
        else:
            return {n: p for n, p in self.plugins.items() if matches(p)}

    def sentiment_plugins(self):
        """ Return only the sentiment plugins """
        return {p: plugin for p, plugin in self.plugins.items() if
                isinstance(plugin, SentimentPlugin)}
