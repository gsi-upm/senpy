What is Senpy?
--------------

Senpy is an open source reference implementation of a linked data model for sentiment and emotion analysis services based on the vocabularies NIF, Marl and Onyx. 

The overall goal of the reference implementation Senpy is easing the adoption of the proposed linked data model for sentiment and emotion analysis services, so that services from different providers become interoperable. With this aim, the design of the reference implementation has focused on its extensibility and reusability. 

A modular approach allows organizations to replace individual components with custom ones developed in-house. Furthermore, organizations can benefit from reusing prepackages modules that provide advanced functionalities, such as algorithms for sentiment and emotion analysis, linked data publication or emotion and sentiment mapping between different providers.

Specifications
==============

The model used in Senpy is based on the following specifications:

* Marl, a vocabulary designed to annotate and describe subjetive opinions expressed on the web or in information systems.
* Onyx, which is built one the same principles as Marl to annotate and describe emotions, and provides interoperability with Emotion Markup Language.
* NIF 2.0, which defines a semantic format and APO for improving interoperability among natural language processing services

Architecture
============

The main component of a sentiment analysis service is the algorithm itself. However, for the algorithm to work, it needs to get the appropriate parameters from the user, format the results according to the defined API, interact with the user whn errors occur or more information is needed, etc.

Senpy proposes a modular and dynamic architecture that allows:

* Implementing different algorithms in a extensible way, yet offering a common interface.
* Offering common services that facilitate development, so developers can focus on implementing new and better algorithms.

The framework consists of two main modules: Senpy core, which is the building block of the service, and Senpy plugins, which consist of the analysis algorithm. The next figure depicts a simplified version of the processes involved in an analysis with the Senpy framework.

.. image:: senpy-architecture.png
  :height: 400px
  :width: 800px
  :scale: 100 %
  :align: center
