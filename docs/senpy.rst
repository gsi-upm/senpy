What is Senpy?
--------------

Senpy is a framework for sentiment and emotion analysis services.
Its goal is to produce analysis services that are interchangeable and fully interoperable.

.. image:: senpy-architecture.png
  :width: 100%
  :align: center

All services built using senpy share a common interface.
This allows users to use them (almost) interchangeably, with the same API and tools, simply by pointing to a different URL or changing a parameter.
The common schema also makes it easier to evaluate the performance of different algorithms and services.
In fact, Senpy has a built-in evaluation API you can use to compare results with different algorithms.

Services can also use the common interface to communicate with each other.
And higher level features can be built on top of these services, such as automatic fusion of results, emotion model conversion, and service discovery.

These benefits are not limited to new services.
The community has developed wrappers for some proprietary and commercial services (such as sentiment140 and Meaning Cloud), so you can consult them as.
Senpy comes with a built-in client in the client package.


To achieve this goal, Senpy uses a Linked Data principled approach, based on the NIF (NLP Interchange Format) specification, and open vocabularies such as Marl and Onyx.
You can learn more about this in :doc:`vocabularies`.

Check out :doc:`development` if you have developed an analysis algorithm (e.g. sentiment analysis) and you want to publish it as a service.
