Usage
-----

The easiest and recommended way is to just use the command-line tool to load your plugins and launch the server.

.. code:: bash

   senpy

Or, alternatively:

.. code:: bash

    python -m senpy


This will create a server with any modules found in the current path. In case you want to load modules that are in a different folders under the same path, use the option `-f .`.

.. code:: bash

    python -m senpy -f .

For more options, see the `--help` page.

Alternatively, you can use the modules included in senpy to build your own application.
