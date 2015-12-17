Developing new plugins
----------------------

Plugins Interface
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

Where can I find more code examples?
????????????????????????????????????

See: `<http://github.com/gsi-upm/senpy-plugins-community>`_.
