Examples
--------

All the examples in this page use the :download:`the main schema <_static/schemas/definitions.json>`.

Simple NIF annotation
.....................
Description
,,,,,,,,,,,
This example covers the basic example in the NIF documentation: `<http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html>`_.

Representation
,,,,,,,,,,,,,,
.. literalinclude:: examples/results/example-basic.json
   :language: json-ld

Sentiment Analysis
.....................
Description
,,,,,,,,,,,

This annotation corresponds to the sentiment analysis of an input. The example shows the sentiment represented according to Marl format.
The sentiments detected are contained in the Sentiments array with their related part of the text.

Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-sentiment.json
   :emphasize-lines: 5-11,20-30
   :language: json-ld

Emotion Analysis
................
Description
,,,,,,,,,,,
This annotation represents the emotion analysis of an input to Senpy. The emotions are contained in the emotions section with the text that refers to following Onyx format and the emotion model defined beforehand.

Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-emotion.json
   :language: json-ld
   :emphasize-lines: 5-11,22-36


