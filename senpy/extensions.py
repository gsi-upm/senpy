import os
import sys
import importlib

from flask import current_app

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

from blueprints import nif_blueprint
from git import Repo, InvalidGitRepositoryError

class Senpy(object):

    def __init__(self, app=None, plugin_folder="plugins"):
        self.app = app
        base_folder = os.path.join(os.path.dirname(__file__), "plugins")

        self.search_folders = (folder for folder in (base_folder, plugin_folder)
                                if folder and os.path.isdir(folder))

        if app is not None:
            self.init_app(app)

    """

        Note: I'm not particularly fond of adding self.app and app.senpy, but
        I can't think of a better way to do it.
    """
    def init_app(self, app, plugin_folder="plugins"):
        app.senpy = self
        #app.config.setdefault('SQLITE3_DATABASE', ':memory:')
        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)
        app.register_blueprint(nif_blueprint)

    def analyse(self, **params):
        if "algorithm" in params:
            algo = params["algorithm"]
            if algo in self.plugins and self.plugins[algo].enabled:
                return self.plugins[algo].plugin.analyse(**params)
        return {"status": 500, "message": "No valid algorithm"}


    def _load_plugin(self, plugin, search_folder, enabled=True):
        sys.path.append(search_folder)
        tmp = importlib.import_module(plugin)
        sys.path.remove(search_folder)
        tmp.path = search_folder
        try:
            repo_path = os.path.join(search_folder, plugin)
            tmp.repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            tmp.repo = None
        if not hasattr(tmp, "enabled"):
            tmp.enabled = enabled
        return tmp


    def _load_plugins(self):
        #print(sys.path)
        #print(search_folder)
        plugins = {}
        for search_folder in self.search_folders:
            for item in os.listdir(search_folder):
                if os.path.isdir(os.path.join(search_folder, item)) \
                        and os.path.exists(
                            os.path.join(search_folder, item, "__init__.py")):
                    plugins[item] = self._load_plugin(item, search_folder)

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
        ctx = stack.top
        if ctx is not None:
            if not hasattr(self, '_plugins'):
                self._plugins = self._load_plugins()
            print("Already plugins")
            return self._plugins

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    sp = Senpy()
    sp.init_app(app)
    with app.app_context():
        sp._load_plugins()
