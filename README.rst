.. image:: img/header.png
   :height: 6em
   :target: http://demos.gsi.dit.upm.es/senpy

.. image:: https://travis-ci.org/gsi-upm/senpy.svg?branch=master
   :target: https://travis-ci.org/gsi-upm/senpy

Senpy lets you create sentiment analysis web services easily, fast and using a well known API.
As a bonus, senpy services use semantic vocabularies (e.g. `NIF <http://persistence.uni-leipzig.org/nlp2rdf/>`_, `Marl <http://www.gsi.dit.upm.es/ontologies/marl>`_, `Onyx <http://www.gsi.dit.upm.es/ontologies/onyx>`_) and formats (turtle, JSON-LD, xml-rdf).

Have you ever wanted to turn your sentiment analysis algorithms into a service?
With senpy, now you can.
It provides all the tools so you just have to worry about improving your algorithms:

`See it in action. <http://demos.gsi.dit.upm.es/senpy>`_

Installation
------------
The stable version can be installed in three ways.

Through PIP
***********

.. code:: bash

   pip install --user senpy

   
Alternatively, you can use the development version:
 
.. code:: bash

   git clone git@github.com:gsi-upm/senpy
   cd senpy
   pip install --user .

If you want to install senpy globally, use sudo instead of the ``--user`` flag.

Docker Image
************
Build the image or use the pre-built one: ``docker run -ti -p 5000:5000 balkian/senpy --host 0.0.0.0 --default-plugins``.

To add custom plugins, add a volume and tell senpy where to find the plugins: ``docker run -ti -p 5000:5000 -v <PATH OF PLUGINS>:/plugins balkian/senpy --host 0.0.0.0 --default-plugins -f /plugins``

Usage
-----

However, the easiest and recommended way is to just use the command-line tool to load your plugins and launch the server.

.. code:: bash

   senpy

or, alternatively:

.. code:: bash

    python -m senpy


This will create a server with any modules found in the current path.
For more options, see the `--help` page.

Alternatively, you can use the modules included in senpy to build your own application.

Deploying on Heroku
-------------------
Use a free heroku instance to share your service with the world.
Just use the example Procfile in this repository, or build your own.


`DEMO on heroku <http://senpy.herokuapp.com>`_


For more information, check out the `documentation <http://senpy.readthedocs.org>`_.
------------------------------------------------------------------------------------


Acknowledgement
---------------
This development has been partially funded by the European Union through the MixedEmotions Project (project number H2020 655632), as part of the `RIA ICT 15 Big data and Open Data Innovation and take-up` programme.


.. image:: img/me.png
    :target: http://mixedemotions-project.eu
    :height: 100px
    :alt: MixedEmotions Logo

.. image:: img/eu-flag.jpg
    :height: 100px
    :target: http://ec.europa.eu/research/participants/portal/desktop/en/opportunities/index.html
