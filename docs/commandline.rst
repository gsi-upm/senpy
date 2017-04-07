Command line
============

In case you want to load modules, which are located in different folders under the root folder, use the next option.

.. code:: bash

    senpy -f .

The default port used by senpy is 5000, but you can change it using the `--port` flag.

.. code:: bash

    senpy --port 8080

Also, the host can be changed where senpy is deployed. The default value is `127.0.0.1`.

.. code:: bash

    senpy --host 0.0.0.0

For more options, see the `--help` page.

Alternatively, you can use the modules included in senpy to build your own application.
