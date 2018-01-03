Advanced plugin definition
--------------------------
In addition to finding plugins defined in source code files, senpy can also load a special type of definition file (`.senpy` files).
This used to be the only mechanism for loading in earlier versions of senpy.

The definition file contains basic information 

Lastly, it is also possible to add new plugins programmatically.

.. contents:: :local:

What is a plugin?
=================

A plugin is a program that, given a text, will add annotations to it.
In practice, a plugin consists of at least two files:

- Definition file: a `.senpy` file that describes the plugin (e.g. what input parameters it accepts, what emotion model it uses).
- Python module: the actual code that will add annotations to each input.

This separation allows us to deploy plugins that use the same code but employ different parameters.
For instance, one could use the same classifier and processing in several plugins, but train with different datasets.
This scenario is particularly useful for evaluation purposes.

The only limitation is that the name of each plugin needs to be unique.

Definition files
================

The definition file complements and overrides the attributes provided by the plugin.
It can be written in YAML or JSON.
The most important attributes are:

* **name**: unique name that senpy will use internally to identify the plugin.
* **module**: indicates the module that contains the plugin code, which will be automatically loaded by senpy.
* **version**
* extra_params: to add parameters to the senpy API when this plugin is requested. Those parameters may be required, and have aliased names. For instance:

  .. code:: yaml

            extra_params:
                hello_param:
                    aliases: # required
                        - hello_param
                        - hello
                    required: true
                    default: Hi you
                    values:
                        - Hi you
                        - Hello y'all
                        - Howdy

A complete example:

.. code:: yaml
          
          name: <Name of the plugin>
          module: <Python file>
          version: 0.1

And the json equivalent:

.. code:: json

          {
            "name": "<Name of the plugin>",
            "module": "<Python file>",
            "version": "0.1"
          }


Example plugin with a definition file
=====================================

In this section, we will implement a basic sentiment analysis plugin.
To determine the polarity of each entry, the plugin will compare the length of the string to a threshold.
This threshold will be included in the definition file.

The definition file would look like this:

.. code:: yaml

          name: helloworld
          module: helloworld
          version: 0.0
          threshold: 10
          description: Hello World

Now, in a file named ``helloworld.py``:

.. code:: python

          #!/bin/env python
          #helloworld.py

          from senpy import AnalysisPlugin
          from senpy import Sentiment


          class HelloWorld(AnalysisPlugin):

              def analyse_entry(entry, params):
                  '''Basically do nothing with each entry'''

                  sentiment = Sentiment()
                  if len(entry.text) < self.threshold:
                      sentiment['marl:hasPolarity'] = 'marl:Positive'
                  else:
                      sentiment['marl:hasPolarity'] = 'marl:Negative'
                  entry.sentiments.append(sentiment)
                  yield entry

The complete code of the example plugin is available `here <https://lab.cluster.gsi.dit.upm.es/senpy/plugin-prueba>`__.
