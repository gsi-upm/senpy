What is Senpy?
--------------

Web services can get really complex: data validation, user interaction, formatting, logging., etc. 
The figure below summarizes the typical features in an analysis service.
Senpy implements all the common blocks, so developers can focus on what really matters: great analysis algorithms that solve real problems.

.. image:: senpy-framework.png
  :width: 60%
  :align: center


Senpy for end users
===================

All services built using senpy share a common interface.
This allows users to use them (almost) interchangeably.
Senpy comes with a :ref:`built-in client`.


Senpy for service developers
============================

Senpy is a framework that turns your sentiment or emotion analysis algorithm into a full blown semantic service.
Senpy takes care of:

  * Interfacing with the user: parameter validation, error handling.
  * Formatting: JSON-LD, Turtle/n-triples input and output, or simple text input
  * Linked Data: senpy results are semantically annotated, using a series of well established vocabularies, and sane default URIs.
  * User interface: a web UI where users can explore your service and test different settings
  * A client to interact with the service. Currently only available in Python.

Sharing your sentiment analysis with the world has never been easier!

Check out the :doc:`plugins` if you have developed an analysis algorithm (e.g. sentiment analysis) and you want to publish it as a service.

Architecture
============

The main component of a sentiment analysis service is the algorithm itself. However, for the algorithm to work, it needs to get the appropriate parameters from the user, format the results according to the defined API, interact with the user whn errors occur or more information is needed, etc.

Senpy proposes a modular and dynamic architecture that allows:

* Implementing different algorithms in a extensible way, yet offering a common interface.
* Offering common services that facilitate development, so developers can focus on implementing new and better algorithms.

The framework consists of two main modules: Senpy core, which is the building block of the service, and Senpy plugins, which consist of the analysis algorithm. The next figure depicts a simplified version of the processes involved in an analysis with the Senpy framework.

.. image:: senpy-architecture.png
  :width: 100%
  :align: center
