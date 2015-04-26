.. image:: logo.png
   :height: 6em
   :align: left

=====================================
`Senpy <http://senpy.herokuapp.com>`_
=====================================
.. image:: https://travis-ci.org/gsi-upm/senpy.svg?branch=master
    :target: https://travis-ci.org/gsi-upm/senpy

Sentiment analysis web services using a common interface: NIF+JSON-LD.

With Senpy, you can easily turn your sentiment analysis algorithm into a web service, just by creating a new plugin.

`DEMO on Heroku <http://senpy.herokuapp.com>`_

Installation
------------
The stable version can be installed via pip:

.. code:: bash

   pip install senpy

   
Alternatively, you can use the development version:
 
.. code:: bash

   git clone git@github.com:gsi-upm/senpy
   cd senpy
   pip install -r requirements.txt 
   
To install it system-wide, use setuptools:

.. code:: bash

   python setup.py install
   
Using
-----

You can use the modules included in senpy to build your own application.
However, the easiest and recommended way is to just use the command-line tool to load your plugins and launch the server.

.. code:: bash

   python -m senpy

This will create a server with any modules found in the current path.
For more options, see the `--help` page.

TO-DO
-----

* Installation instructions
* Improve documentation and generate it with Sphinx
* ReadTheDocs
* Improve README


Acknowledgement
---------------
EUROSENTIMENT PROJECT
Grant Agreement no: 296277
Starting date: 01/09/2012
Project duration: 24 months

.. image:: logo_grande.png
    :target: logo_grande.png
    :width: 100px
    :alt: Eurosentiment Logo

.. image:: logo_fp7.gif
    :width: 100px
    :target: logo_fp7.gif
