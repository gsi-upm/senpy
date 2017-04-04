Developing new plugins
----------------------
This document describes how to develop a new analysis plugin. For an example of conversion plugins, see :doc:`conversion`.

A more step-by-step tutorial with slides is available `here <https://lab.cluster.gsi.dit.upm.es/senpy/senpy-tutorial>`__ 

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

Plugin Definition files
=======================

The definition file contains all the attributes of the plugin, and can be written in YAML or JSON.
When the server is launched, it will recursively search for definition files in the plugin folder (the current folder, by default).
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

  Parameter validation will fail if a required parameter without a default has not been provided, or if the definition includes a set of values and the provided one does not match one of them.


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


Plugins Code
============

The basic methods in a plugin are:

* __init__
* activate: used to load memory-hungry resources
* deactivate: used to free up resources
* analyse_entry: called in every user requests. It takes two parameters: ``Entry``, the entry object, and ``params``, the parameters supplied by the user. It should yield one or more ``Entry`` objects.

Plugins are loaded asynchronously, so don't worry if the activate method takes too long. The plugin will be marked as activated once it is finished executing the method.

Entries
=======

Entries are objects that can be annotated.
By default, entries are `NIF contexts <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html>`_ represented in JSON-LD format.
Annotations are added to the object like this:

.. code:: python

   entry = Entry()
   entry.vocabulary__annotationName = 'myvalue'
   entry['vocabulary:annotationName'] = 'myvalue'
   entry['annotationNameURI'] = 'myvalue'

Where vocabulary is one of the prefixes defined in the default senpy context, and annotationURI is a full URI.
The value may be any valid JSON-LD dictionary.
For simplicity, senpy includes a series of models by default in the ``senpy.models`` module.


Example plugin
==============

In this section, we will implement a basic sentiment analysis plugin.
To determine the polarity of each entry, the plugin will compare the length of the string to a threshold.
This threshold will be included in the definition file.

The definition file would look like this:

.. code:: yaml

          name: helloworld
          module: helloworld
          version: 0.0
          threshold: 10


Now, in a file named ``helloworld.py``:

.. code:: python

          #!/bin/env python
          #helloworld.py

          from senpy.plugins import SenpyPlugin
          from senpy.models import Sentiment


          class HelloWorld(SenpyPlugin):

              def analyse_entry(entry, params):
                  '''Basically do nothing with each entry'''

                  sentiment = Sentiment()
                  if len(entry.text) < self.threshold:
                      sentiment['marl:hasPolarity'] = 'marl:Positive'
                  else:
                      sentiment['marl:hasPolarity'] = 'marl:Negative'
                  entry.sentiments.append(sentiment)
                  yield entry


F.A.Q.
======
What annotations can I use?
???????????????????????????

You can add almost any annotation to an entry.
The most common use cases are covered in the :doc:`schema`.


Why does the analyse function yield instead of return?
??????????????????????????????????????????????????????

This is so that plugins may add new entries to the response or filter some of them.
For instance, a `context detection` plugin may add a new entry for each context in the original entry.
On the other hand, a conveersion plugin may leave out those entries that do not contain relevant information.


If I'm using a classifier, where should I train it?
???????????????????????????????????????????????????

Training a classifier can be time time consuming. To avoid running the training unnecessarily, you can use ShelfMixin to store the classifier. For instance:

.. code:: python

          from senpy.plugins import ShelfMixin, SenpyPlugin

          class MyPlugin(ShelfMixin, SenpyPlugin):
              def train(self):
                  ''' Code to train the classifier
                  '''
                  # Here goes the code
                  # ...
                  return classifier

              def activate(self):
                  if 'classifier' not in self.sh:
                      classifier = self.train()
                      self.sh['classifier'] = classifier
                  self.classifier = self.sh['classifier']
              
              def deactivate(self):
                  self.close()

You can speficy a 'shelf_file' in your .senpy file. By default the ShelfMixin creates a file based on the plugin name and stores it in that plugin's folder.

I want to implement my service as a plugin, How i can do it?
????????????????????????????????????????????????????????????

This example ilustrate how to implement the Sentiment140 service as a plugin in senpy

.. code:: python

          class Sentiment140Plugin(SentimentPlugin):
              def analyse_entry(self, entry, params):
                  text = entry.text
                  lang = params.get("language", "auto")
                  res = requests.post("http://www.sentiment140.com/api/bulkClassifyJson",
                                      json.dumps({"language": lang,
                                                  "data": [{"text": text}]
                                                  }
                                                 )
                                      )

                  p = params.get("prefix", None)
                  polarity_value = self.maxPolarityValue*int(res.json()["data"][0]
                                                             ["polarity"]) * 0.25
                  polarity = "marl:Neutral"
                  neutral_value = self.maxPolarityValue / 2.0
                  if polarity_value > neutral_value:
                      polarity = "marl:Positive"
                  elif polarity_value < neutral_value:
                      polarity = "marl:Negative"

                  sentiment = Sentiment(id="Sentiment0",
                                      prefix=p,
                                      marl__hasPolarity=polarity,
                                      marl__polarityValue=polarity_value)
                  sentiment.prov__wasGeneratedBy = self.id
                  entry.sentiments.append(sentiment)
                  yield entry


Where can I define extra parameters to be introduced in the request to my plugin?
?????????????????????????????????????????????????????????????????????????????????

You can add these parameters in the definition file under the attribute "extra_params" : "{param_name}". The name of the parameter has new attributes-value pairs. The basic attributes are:

* aliases: the different names which can be used in the request to use the parameter.
* required: this option is a boolean and indicates if the parameters is binding in operation plugin.
* options: the different values of the paremeter.
* default: the default value of the parameter, this is useful in case the paremeter is required and you want to have a default value.

.. code:: python

          "extra_params": {
             "language": {
                "aliases": ["language", "l"],
                "required": true,
                "options": ["es","en"],
                "default": "es"
             }
          }

This example shows how to introduce a parameter associated with language.
The extraction of this paremeter is used in the analyse method of the Plugin interface.

.. code:: python

          lang = params.get("language")

Where can I set up variables for using them in my plugin?
?????????????????????????????????????????????????????????

You can add these variables in the definition file with the structure of attribute-value pairs.

Every field added to the definition file is available to the plugin instance.

Can I activate a DEBUG mode for my plugin?
???????????????????????????????????????????

You can activate the DEBUG mode by the command-line tool using the option -d.

.. code:: bash

   senpy -d


Additionally, with the ``--pdb`` option you will be dropped into a pdb post mortem shell if an exception is raised.

.. code:: bash

   senpy --pdb


Where can I find more code examples?
????????????????????????????????????

See: `<http://github.com/gsi-upm/senpy-plugins-community>`_.
