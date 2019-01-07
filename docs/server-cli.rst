Server
======

The senpy server is launched via the `senpy` command:

.. code:: text

    usage: senpy [-h] [--level logging_level] [--log-format log_format] [--debug]
                [--no-default-plugins] [--host HOST] [--port PORT]
                [--plugins-folder PLUGINS_FOLDER] [--only-install] [--only-test]
                [--test] [--only-list] [--data-folder DATA_FOLDER]
                [--no-threaded] [--no-deps] [--version] [--allow-fail]

    Run a Senpy server

    optional arguments:
      -h, --help            show this help message and exit
      --level logging_level, -l logging_level
                            Logging level
      --log-format log_format
                            Logging format
      --debug, -d           Run the application in debug mode
      --no-default-plugins  Do not load the default plugins
      --host HOST           Use 0.0.0.0 to accept requests from any host.
      --port PORT, -p PORT  Port to listen on.
      --plugins-folder PLUGINS_FOLDER, -f PLUGINS_FOLDER
                            Where to look for plugins.
      --only-install, -i    Do not run a server, only install plugin dependencies
      --only-test           Do not run a server, just test all plugins
      --test, -t            Test all plugins before launching the server
      --only-list, --list   Do not run a server, only list plugins found
      --data-folder DATA_FOLDER, --data DATA_FOLDER
                            Where to look for data. It be set with the SENPY_DATA
                            environment variable as well.
      --no-threaded         Run the server without threading
      --no-deps, -n         Skip installing dependencies
      --version, -v         Output the senpy version and exit
      --allow-fail, --fail  Do not exit if some plugins fail to activate


When launched, the server will recursively look for plugins in the specified plugins folder (the current working directory by default).
For every plugin found, it will download its dependencies, and try to activate it.
The default server includes a playground and an endpoint with all plugins found.

Let's run senpy with the default plugins:

.. code:: bash

    senpy -f .

Now open your browser and go to `http://localhost:5000 <http://localhost:5000>`_, where you should be greeted by the senpy playground:

.. image:: senpy-playground.png
   :width: 100%
   :alt: Playground

The playground is a user-friendly way to test your plugins, but you can always use the service directly:  `http://localhost:5000/api?input=hello <http://localhost:5000/api?input=hello>`_.


By default, senpy will listen only on `127.0.0.1`.
That means you can only access the API from your PC (i.e. localhost).
You can listen on a different address using the `--host` flag (e.g., 0.0.0.0, to allow any computer to access it).
The default port is 5000.
You can change it with the `--port` flag. 

For instance, to accept connections on port 6000 on any interface:

.. code:: bash

    senpy --host 0.0.0.0 --port 6000

For more options, see the `--help` page.
