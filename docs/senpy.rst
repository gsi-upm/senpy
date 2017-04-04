What is Senpy?
--------------

Senpy is a framework that turns your sentiment or emotion analysis algorithm into a full blown semantic service.
Senpy takes care of:

  * Interfacing with the user: parameter validation, error handling.
  * Formatting: JSON-LD, Turtle/n-triples input and output, or simple text input
  * Linked Data: senpy results are semantically annotated, using a series of well established vocabularies, and sane default URIs.
  * User interface: a web UI where users can explore your service and test different settings
  * A client to interact with the service. Currently only available in Python.

Sharing your sentiment analysis with the world has never been easier!

Senpy for service developers
============================

Check out the :doc:`plugins` if you have developed an analysis algorithm (e.g. sentiment analysis) and you want to publish it as a service.

Senpy for end users
===================

All services built using senpy share a common interface.
This allows users to use them (almost) interchangeably.
Senpy comes with a :ref:`built-in client`.


.. toctree::
    :caption: Interested? Check out senpy's:
 
    architecture

