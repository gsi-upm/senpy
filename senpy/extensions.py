import os
import sys
import imp
import logging

logger = logging.getLogger(__name__)

from .plugins import SentimentPlugin, EmotionPlugin

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

from .blueprints import nif_blueprint
from git import Repo, InvalidGitRepositoryError


class Senpy(object):
    """ Default Senpy extension for Flask """

    def __init__(self, app=None, plugin_folder="plugins"):
        self.app = app
        base_folder = os.path.join(os.path.dirname(__file__), "plugins")

        self._search_folders = set()
        self._outdated = True

        for folder in (base_folder, plugin_folder):
            self.add_folder(folder)

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
        if os.path.isdir(folder):
            self._search_folders.add(folder)
            self._outdated = True
            return True
        else:
            return False


    def analyse(self, **params):
        algo = None
        logger.debug("analysing with params: {}".format(params))
        if "algorithm" in params:
            algo = params["algorithm"]
        elif self.plugins:
            algo = self.default_plugin
        if algo in self.plugins and self.plugins[algo].enabled:
            plug = self.plugins[algo]
            resp = plug.analyse(**params)
            resp.analysis.append(plug.jsonable())
            return resp
        else:
            return {"status": 400, "message": "The algorithm '{}' is not valid".format(algo) }

    @property
    def default_plugin(self):
        candidates = self.filter_plugins(enabled=True)
        if len(candidates)>1:
            candidate = candidates.keys()[0]
            logger.debug("Default: {}".format(candidate))
            return candidate
        else:
            return None

    def parameters(self, algo):
        return getattr(self.plugins.get(algo or self.default_plugin), "params", {})

    def enable_plugin(self, plugin):
        self.plugins[plugin].enable()

    def disable_plugin(self, plugin):
        self.plugins[plugin].disable()

    def reload_plugin(self, plugin):
        logger.debug("Reloading {}".format(plugin))
        plug = self.plugins[plugin]
        nplug = self._load_plugin(plug.module, plug.path)
        del self.plugins[plugin]
        self.plugins[nplug.name] = nplug

    def _load_plugin(self, plugin, search_folder, enabled=True):
        logger.debug("Loading plugins")
        sys.path.append(search_folder)
        (fp, pathname, desc) = imp.find_module(plugin)
        try:
            tmp = imp.load_module(plugin, fp, pathname, desc).plugin
            sys.path.remove(search_folder)
            tmp.path = search_folder
            try:
                repo_path = os.path.join(search_folder, plugin)
                tmp.repo = Repo(repo_path)
            except InvalidGitRepositoryError:
                tmp.repo = None
            if not hasattr(tmp, "enabled"):
                tmp.enabled = enabled
            tmp.module = plugin
        except Exception as ex:
            tmp = None
            logger.debug("Exception importing {}: {}".format(plugin, ex))
        return tmp


    def _load_plugins(self):
        plugins = {}
        for search_folder in self._search_folders:
            for item in os.listdir(search_folder):
                if os.path.isdir(os.path.join(search_folder, item)) \
                        and os.path.exists(
                            os.path.join(search_folder, item, "__init__.py")):
                    plugin = self._load_plugin(item, search_folder)
                    if plugin:
                        plugins[plugin.name] = plugin

        self._outdated = False
        return plugins

    def teardown(self, exception):
        pass

    def enable_all(self):
        for plugin in self.plugins:
            self.enable_plugin(plugin)

    def enable_plugin(self, item):
        self.plugins[item].enabled = True

    def disable_plugin(self, item):
        self.plugins[item].enabled = False

    @property
    def plugins(self):
        """ Return the plugins registered for a given application.  """
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'senpy_plugins') or self._outdated:
                ctx.senpy_plugins = self._load_plugins()
            return ctx.senpy_plugins

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
            return {n:p for n, p in self.plugins.items() if matches(p)}

    def sentiment_plugins(self):
        """ Return only the sentiment plugins """
        return {p:plugin for p, plugin in self.plugins.items() if
                isinstance(plugin, SentimentPlugin)}


if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    sp = Senpy()
    sp.init_app(APP)
    with APP.app_context():
        sp._load_plugins()
