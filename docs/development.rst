Developing new services
-----------------------

Developing web services can be hard.
A text analysis service must implement all the typical features, such as: extraction of parameters, validation, format conversion, visualization...

Senpy implements all the common blocks, so developers can focus on what really matters: great analysis algorithms that solve real problems.
Among other things, Senpy takes care of these tasks:

  * Interfacing with the user: parameter validation, error handling.
  * Formatting: JSON-LD, Turtle/n-triples input and output, or simple text input
  * Linked Data: senpy results are semantically annotated, using a series of well established vocabularies, and sane default URIs.
  * User interface: a web UI where users can explore your service and test different settings
  * A client to interact with the service. Currently only available in Python.

You only need to provide the algorithm to turn a piece of text into an annotation
Sharing your sentiment analysis with the world has never been easier!

.. toctree::
    :maxdepth: 1

    server-cli
    plugins-quickstart
    plugins-faq
    plugins-definition
