Quickstart for service developers
=================================
 
This document contains the minimum to get you started with developing new services using Senpy.

For an example of conversion plugins, see :doc:`conversion`.
For a description of definition files, see :doc:`plugins-definition`.

A more step-by-step tutorial with slides is available `here <https://lab.gsi.upm.es/senpy/senpy-tutorial>`__ 

.. contents:: :local:

Installation
############

First of all, you need to install the package.
See :doc:`installation` for instructions.
Once installed, the `senpy` command should be available. 

Architecture
############

The main component of a sentiment analysis service is the algorithm itself. However, for the algorithm to work, it needs to get the appropriate parameters from the user, format the results according to the defined API, interact with the user whn errors occur or more information is needed, etc.

Senpy proposes a modular and dynamic architecture that allows:

* Implementing different algorithms in a extensible way, yet offering a common interface.
* Offering common services that facilitate development, so developers can focus on implementing new and better algorithms.

The framework consists of two main modules: Senpy core, which is the building block of the service, and Senpy plugins, which consist of the analysis algorithm. The next figure depicts a simplified version of the processes involved in an analysis with the Senpy framework.

.. image:: senpy-architecture.png
  :width: 100%
  :align: center


What is a plugin?
#################

A plugin is a python object that can process entries. Given an entry, it will modify it, add annotations to it, or generate new entries.


What is an entry?
#################

Entries are objects that can be annotated.
In general, they will be a piece of text.
By default, entries are `NIF contexts <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html>`_ represented in JSON-LD format.
It is a dictionary/JSON object that looks like this:

  .. code:: python

            {
               "@id": "<unique identifier or blank node name>",
               "nif:isString": "input text",
               "sentiments": [ {
                     ...
               }
               ],
               ...
            }

Annotations are added to the object like this:

.. code:: python

   entry = Entry()
   entry.vocabulary__annotationName = 'myvalue'
   entry['vocabulary:annotationName'] = 'myvalue'
   entry['annotationNameURI'] = 'myvalue'

Where vocabulary is one of the prefixes defined in the default senpy context, and annotationURI is a full URI.
The value may be any valid JSON-LD dictionary.
For simplicity, senpy includes a series of models by default in the ``senpy.models`` module.

Plugins Code
############

The basic methods in a plugin are:

* analyse_entry: called in every user requests. It takes two parameters: ``Entry``, the entry object, and ``params``, the parameters supplied by the user. It should yield one or more ``Entry`` objects.
* activate: used to load memory-hungry resources. For instance, to train a classifier.
* deactivate: used to free up resources when the plugin is no longer needed.

Plugins are loaded asynchronously, so don't worry if the activate method takes too long. The plugin will be marked as activated once it is finished executing the method.

