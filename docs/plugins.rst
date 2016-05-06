Developing new plugins
----------------------
Each plugin represents a different analysis process.There are two types of files that are needed by senpy for loading a plugin:

Plugins Interface
=======
- Definition file, has the ".senpy" extension.
- Code file, is a python file.

Plugins Definitions
===================

The definition file can be written in JSON or YAML, where the data representation consists on attribute-value pairs.
The principal attributes are:

* name: plugin name used in senpy to call the plugin.
* module: indicates the module that will be loaded

.. code:: python

          {
            "name" : "senpyPlugin",
            "module" : "{python code file}"
          }

.. code:: python
          
          name: senpyPlugin
          module: {python code file}

Plugins Code
=================

The basic methods in a plugin are:

* __init__
* activate: used to load memory-hungry resources
* deactivate: used to free up resources
* analyse: called in every user requests. It takes in the parameters supplied by a user and should return a senpy Response.

Plugins are loaded asynchronously, so don't worry if the activate method takes too long. The plugin will be marked as activated once it is finished executing the method.

F.A.Q.
======
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
              def analyse(self, **params):
                  lang = params.get("language", "auto")
                  res = requests.post("http://www.sentiment140.com/api/bulkClassifyJson",
                                      json.dumps({"language": lang,
                                                  "data": [{"text": params["input"]}]
                                                  }
                                                 )
                                      )

                  p = params.get("prefix", None)
                  response = Results(prefix=p)
                  polarity_value = self.maxPolarityValue*int(res.json()["data"][0]
                                                             ["polarity"]) * 0.25
                  polarity = "marl:Neutral"
                  neutral_value = self.maxPolarityValue / 2.0
                  if polarity_value > neutral_value:
                      polarity = "marl:Positive"
                  elif polarity_value < neutral_value:
                      polarity = "marl:Negative"

                  entry = Entry(id="Entry0",
                                nif__isString=params["input"])
                  sentiment = Sentiment(id="Sentiment0",
                                      prefix=p,
                                      marl__hasPolarity=polarity,
                                      marl__polarityValue=polarity_value)
                  sentiment.prov__wasGeneratedBy = self.id
                  entry.sentiments = []
                  entry.sentiments.append(sentiment)
                  entry.language = lang
                  response.entries.append(entry)
                  return response


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

You can add these variables in the definition file with the extracture of attribute-value pair.

Once you have added your variables, the next step is to extract them into the plugin. The plugin's __init__ method has a parameter called `info` where you can extract the values of the variables. This info parameter has the structure of a python dictionary.

Can I activate a DEBUG mode for my plugin?
???????????????????????????????????????????

You can activate the DEBUG mode by the command-line tool using the option -d.

.. code:: bash

   python -m senpy -d

Where can I find more code examples?
????????????????????????????????????

See: `<http://github.com/gsi-upm/senpy-plugins-community>`_.
