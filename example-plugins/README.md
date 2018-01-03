This is a collection of plugins that exemplify certain aspects of plugin development with senpy.
In ascending order of complexity, there are:

* Basic: a very basic analysis that does sentiment analysis based on emojis.
* Configurable: a version of `basic` with a configurable map of emojis for each sentiment.
* Parameterized: like `basic_info`, but users set the map in each query (via `extra_parameters`).
* mynoop: shows how to add a definition file with external requirements for a plugin. Doing this with a python-only module would require moving all imports of the requirements to their functions, which is considered bad practice.
* Async: a barebones example of training a plugin and analyzing data in parallel.

All of the plugins in this folder include a set of test cases and they are periodically tested with the latest version of senpy.

Additioanlly, for an example of stand-alone plugin that can be tested and deployed with docker, take a look at: lab.cluster.gsi.dit.upm.es/senpy/plugin-example
 bbm
