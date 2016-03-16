Usage
-----

The easiest and recommended way is to just use the command-line tool to load your plugins and launch the server.

.. code:: bash

   senpy

Or, alternatively:

.. code:: bash

    python -m senpy


This will create a server with any modules found in the current path.

Useful command-line options
=================

In case you want to load modules that are in different folders under the same path, use the next option.

.. code:: bash

    python -m senpy -f .

The default port used by senpy is 5000, but you can change it using the option `--port`.

.. code:: bash

    python -m senpy --port 8080

Also, the host can be changed where senpy is deployed. The default value is `127.0.0.1`.

.. code:: bash

    python -m senpy --host 125.1.2.3

For more options, see the `--help` page.

Alternatively, you can use the modules included in senpy to build your own application.
