F.A.Q.
======

.. contents:: :local:



What are annotations?
#####################
They are objects just like entries.
Senpy ships with several default annotations, including ``Sentiment`` and ``Emotion``.


What's a plugin made of?
########################

When receiving a query, senpy selects what plugin or plugins should process each entry, and in what order.
It also makes sure the every entry and the parameters provided by the user meet the plugin requirements.

Hence, two parts are necessary: 1) the code that will process the entry, and 2) some attributes and metadata that will tell senpy how to interact with the plugin.

In practice, this is what a plugin looks like, tests included:


.. literalinclude:: ../example-plugins/rand_plugin.py
   :emphasize-lines: 5-11
   :language: python


The lines highlighted contain some information about the plugin.
In particular, the following information is mandatory:

* A unique name for the class. In our example, sentiment-random.
* The subclass/type of plugin. This is typically either `SentimentPlugin` or `EmotionPlugin`. However, new types of plugin can be created for different annotations. The only requirement is that these new types inherit from `senpy.Analysis`
* A description of the plugin. This can be done simply by adding a doc to the class.
* A version, which should get updated.
* An author name.


How does senpy find modules?
############################

Senpy looks for files of two types:

* Python files of the form `senpy_<NAME>.py` or `<NAME>_plugin.py`. In these files, it will look for: 1) Instances that inherit from `senpy.Plugin`, or subclasses of `senpy.Plugin` that can be initialized without a configuration file. i.e. classes that contain all the required attributes for a plugin.
* Plugin definition files (see :doc:`plugins-definition`)

How can I define additional parameters for my plugin?
#####################################################

Your plugin may ask for additional parameters from users by using the attribute ``extra_params`` in your plugin definition.
It takes a dictionary, where the keys are the name of the argument/parameter, and the value has the following fields:

* aliases: the different names which can be used in the request to use the parameter.
* required: if set to true, users need to provide this parameter unless a default is set.
* options: the different acceptable values of the parameter (i.e. an enum). If set, the value provided must match one of the options.
* default: the default value of the parameter, if none is provided in the request.

.. code:: python

          "extra_params":{
             "language": {
                "aliases": ["language", "lang", "l"],
                "required": True,
                "options": ["es", "en"],
                "default": "es"
                }
             }



How should I load external data and files
#########################################

Most plugins will need access to files (dictionaries, lexicons, etc.).
These files are usually heavy or under a license that does not allow redistribution.
For this reason, senpy has a `data_folder` that is separated from the source files.
The location of this folder is controlled programmatically or by setting the `SENPY_DATA` environment variable.
You can use the `self.path(filepath)` function to get the path of a given `filepath` within the data folder.

Plugins have a convenience function `self.open` which will automatically look for the file if it exists, or open a new one if it doesn't:


.. code:: python

          import os


          class PluginWithResources(AnalysisPlugin):
              file_in_data = <FILE PATH>
              file_in_sources = <FILE PATH>

              def on activate(self):
                  with self.open(self.file_in_data) as f:
                      self._classifier = train_from_file(f)
                  file_in_source = os.path.join(self.get_folder(), self.file_in_sources)
                  with self.open(file_in_source) as f:
                      pass

         
It is good practice to specify the paths of these files in the plugin configuration, so the same code can be reused with different resources.


Can I build a docker image for my plugin?
#########################################

Add the following dockerfile to your project to generate a docker image with your plugin:

.. code:: dockerfile

   FROM gsiupm/senpy

Once you make sure your plugin works with a specific version of senpy, modify that file to make sure your build will work even if senpy gets updated.
e.g.:


.. code:: dockerfile

   FROM gsiupm/senpy:1.0.1

     
This will copy your source folder to the image, and install all dependencies.
Now, to build an image:

.. code:: shell

   docker build . -t gsiupm/exampleplugin

And you can run it with:

.. code:: shell

   docker run -p 5000:5000 gsiupm/exampleplugin


If the plugin uses non-source files (:ref:`How should I load external data and files`), the recommended way is to use `SENPY_DATA` folder.
Data can then be mounted in the container or added to the image.
The former is recommended for open source plugins with licensed resources, whereas the latter is the most convenient and can be used for private images.

Mounting data:

.. code:: bash

   docker run -v $PWD/data:/data gsiupm/exampleplugin

Adding data to the image:

.. code:: dockerfile

   FROM gsiupm/senpy:1.0.1
   COPY data /

What annotations can I use?
###########################

You can add almost any annotation to an entry.
The most common use cases are covered in the :doc:`apischema`.


Why does the analyse function yield instead of return?
######################################################

This is so that plugins may add new entries to the response or filter some of them.
For instance, a chunker may split one entry into several.
On the other hand, a conversion plugin may leave out those entries that do not contain relevant information.


If I'm using a classifier, where should I train it?
###################################################

Training a classifier can be time time consuming. To avoid running the training unnecessarily, you can use ShelfMixin to store the classifier. For instance:

.. code:: python

          from senpy.plugins import ShelfMixin, AnalysisPlugin

          class MyPlugin(ShelfMixin, AnalysisPlugin):
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


By default the ShelfMixin creates a file based on the plugin name and stores it in that plugin's folder.
However, you can manually specify a 'shelf_file' in your .senpy file.

Shelves may get corrupted if the plugin exists unexpectedly.
A corrupt shelf prevents the plugin from loading.
If you do not care about the data in the shelf, you can force your plugin to remove the corrupted file and load anyway, set the  'force_shelf' to True in your plugin and start it again.

How can I turn an external service into a plugin?
#################################################

This example ilustrate how to implement a plugin that accesses the Sentiment140 service.

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
                  sentiment.prov(self)
                  entry.sentiments.append(sentiment)
                  yield entry


How can I activate a DEBUG mode for my plugin?
###############################################

You can activate the DEBUG mode by the command-line tool using the option -d.

.. code:: bash

   senpy -d


Additionally, with the ``--pdb`` option you will be dropped into a pdb post mortem shell if an exception is raised.

.. code:: bash

   python -m pdb yourplugin.py

Where can I find more code examples?
####################################

See: `<http://github.com/gsi-upm/senpy-plugins-community>`_.
