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
===========================

In case you want to load modules, which are located in different folders under the root folder, use the next option.

.. code:: bash

    python -m senpy -f .

The default port used by senpy is 5000, but you can change it using the option `--port`.

.. code:: bash

    python -m senpy --port 8080

Also, the host can be changed where senpy is deployed. The default value is `127.0.0.1`.

.. code:: bash

    python -m senpy --host 0.0.0.0

For more options, see the `--help` page.

Alternatively, you can use the modules included in senpy to build your own application.

Senpy server
============

Once the server is launched, there is a basic endpoint in the server, which provides a playground to use the plugins that have been loaded.

In case you want to know the different endpoints of the server, there is more information available in the NIF API section_.

Video example
=============

This video shows how to use senpy through command-line tool.

https://asciinema.org/a/9uwef1ghkjk062cw2t4mhzpyk

Request example in python
=========================

This example shows how to make a request to a plugin.

.. code:: python

    import requests
    import json

    r = requests.get('http://127.0.0.1:5000/api/?algo=rand&i=Testing')
    response = r.content.decode('utf-8')
    response_json = json.loads(response)



.. _section: http://senpy.readthedocs.org/en/latest/api.html

