This is a collection of plugins that exemplify certain aspects of plugin development with senpy.

The first series of plugins are the `basic` ones.
Their starting point is a classification function defined in `basic.py`.
They all include testing and running them as a script will run all tests.
In ascending order of customization, the plugins are:

* Basic is the simplest plugin of all. It leverages the `SentimentBox` Plugin class to create a plugin out of a classification method, and `MappingMixin` to convert the labels from (`pos`, `neg`) to (`marl:Positive`, `marl:Negative`
* Basic_box is just like the previous one, but replaces the mixin with a custom function.
* Basic_configurable is a version of `basic` with a configurable map of emojis for each sentiment.
* Basic_parameterized like `basic_info`, but users set the map in each query (via `extra_parameters`).
* Basic_analyse\_entry uses the more general `analyse_entry` method and adds the annotations individually.


In rest of the plugins show advanced topics:

* mynoop: shows how to add a definition file with external requirements for a plugin. Doing this with a python-only module would require moving all imports of the requirements to their functions, which is considered bad practice.
* Async: a barebones example of training a plugin and analyzing data in parallel.

All of the plugins in this folder include a set of test cases and they are periodically tested with the latest version of senpy.

Additioanlly, for an example of stand-alone plugin that can be tested and deployed with docker, take a look at: lab.gsi.upm.es/senpy/plugin-example
 bbm
