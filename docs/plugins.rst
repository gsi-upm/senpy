Developing new plugins
----------------------

There are two types of files that were needed by senpy for loading a plugin:

- *.senpy: this file is the builder of the plugin.
- *.py: this file is the interface of the plugin.

Plugins Builder
================

The structure of this files is similar to a python dictionary, where the data representation consists on attribute-value pairs.
The principal attributes are:

* name: plugin name used in senpy to call the plugin.
* module: name of the file where the interface is written (*.py)

.. code:: python

          {
            "name" : "senpyPlugin",
            "module" : "{python file}"
          }

You can use another attributes such as `description`, `author`, `version`, etc.


Plugins Interface
=================

The basic methods in a plugin are:

* __init__
* activate: used to load memory-hungry resources
* deactivate: used to free up resources
* analyse: called in every user requests. It takes in the parameters supplied by a user and should return a senpy Results.

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

Where can I define extra parameters to be introduced in the request to my plugin?
?????????????????????????????????????????????????????????????????????????????????

You can add these parameters in the *.senpy file under the attribute "extra_params" : "{param_name}". The name of the parameter is going to act as another python dictionary with the next attributes:

* aliases: the different names which can be used in the request to use the parameter.
* required: this option is a boolean and indicates if the parameters is binding in operation plugin.
* options: the different values of the paremeter.
* default: the default value which can have the parameter, this is useful in case the paremeter is required and you want to have a default value.

.. code:: python

          "extra_params": {
             "language": {
                "aliases": ["language", "l"],
                "required": true,
                "options": ["es"],
                "default": "es"
             }
          }

This example shows how to introduce a parameter associated language.
The extraction of this paremeter is used in the analyse method of the Plugin interface.

.. code:: python

          lang = params.get("language")

Where can I set up variables for using them in my plugin?
?????????????????????????????????????????????????????????

You can add these variables in the *.senpy with:  {variable_name} : {variable_value}.

Once you have added your variables, the next step is to extract them in the plugin. The plugin's __init__ method has a parameter called `info` where you can extract the values of the variables. This info parameter has the structure of a python dictionary.

Can I activate a DEBUGG mode for my plugin?
???????????????????????????????????????????

You can activate the DEBUGG mode by the command-line tool using the option -d.

.. code:: bash

   python -m senpy -d

Where can I find more code examples?
????????????????????????????????????

See: `<http://github.com/gsi-upm/senpy-plugins-community>`_.
