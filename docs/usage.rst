Usage
-----

First of all, you need to install the package.
See :doc:`installation` for installation instructions.
Once installed, the `senpy` command should be available. 

Useful command-line options
===========================

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

Senpy server
============

Once the server is launched, there is a basic endpoint in the server, which provides a playground to use the plugins that have been loaded.

In case you want to know the different endpoints of the server, there is more information available in the NIF API section_.

CLI demo
========

This video shows how to use senpy through command-line tool.

.. image:: https://asciinema.org/a/9uwef1ghkjk062cw2t4mhzpyk.png
   :width: 100%
   :target: https://asciinema.org/a/9uwef1ghkjk062cw2t4mhzpyk
   :alt: CLI demo


Built-in client
===============

This example shows how to make a request to the default plugin:

.. code:: python

    from senpy.client import Client

    c = Client('http://127.0.0.1:5000/api/')
    r = c.analyse('hello world')

    for entry in r.entries:
          print('{} -> {}'.format(entry.text, entry.emotions))



.. _section: http://senpy.readthedocs.org/en/latest/api.html


Conversion
==========
See :doc:`conversion`
