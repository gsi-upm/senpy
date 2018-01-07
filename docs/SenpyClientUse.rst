
Client
======

Demo Endpoint
-------------

Import Client and send a request

.. code:: python

    from senpy.client import Client
    
    c = Client('http://latest.senpy.cluster.gsi.dit.upm.es/api')
    r = c.analyse('I like Pizza', algorithm='sentiment140')

Print response

.. code:: python

    for entry in r.entries:
          print('{} -> {}'.format(entry['text'], entry['sentiments'][0]['marl:hasPolarity']))


.. parsed-literal::

    I like Pizza -> marl:Positive


Obtain a list of available plugins

.. code:: python

    for plugin in c.request('/plugins')['plugins']:
        print(plugin['name'])


.. parsed-literal::

    emoRand
    rand
    sentiment140


Local Endpoint
--------------

Run a docker container with Senpy image and default plugins

.. code::

    docker run -ti --name 'SenpyEndpoint' -d -p 5000:5000 gsiupm/senpy:0.8.6 --host 0.0.0.0 --default-plugins


.. parsed-literal::

    a0157cd98057072388bfebeed78a830da7cf0a796f4f1a3fd9188f9f2e5fe562


Import client and send a request to localhost

.. code:: python

    c_local = Client('http://127.0.0.1:5000/api')
    r = c_local.analyse('Hello world', algorithm='sentiment140')

Print response

.. code:: python

    for entry in r.entries:
          print('{} -> {}'.format(entry['text'], entry['sentiments'][0]['marl:hasPolarity']))


.. parsed-literal::

    Hello world -> marl:Neutral


Obtain a list of available plugins deployed locally

.. code:: python

    c_local.plugins().keys()


.. parsed-literal::

    rand
    sentiment140
    emoRand


Stop the docker container

.. code:: python

    !docker stop SenpyEndpoint
    !docker rm SenpyEndpoint


.. parsed-literal::

    SenpyEndpoint
    SenpyEndpoint

