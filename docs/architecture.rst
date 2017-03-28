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
