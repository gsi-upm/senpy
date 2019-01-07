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
   :emphasize-lines: 5-10,25-33
   :language: json-ld

Suggestion Mining
.................
Description
,,,,,,,,,,,
The suggestions schema represented below shows the suggestions detected in the text. Within it, we can find the NIF fields highlighted that corresponds to the text of the detected suggestion. 

Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-suggestion.json
   :emphasize-lines: 5-8,22-27
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
   :emphasize-lines: 5-8,25-37

Named Entity Recognition
........................
Description
,,,,,,,,,,,
The Named Entity Recognition is represented as follows. In this particular case, it can be seen within the entities array the entities recognised. For the example input, Microsoft and Windows Phone are the ones detected. 
Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-ner.json
   :emphasize-lines: 5-8,19-34
   :language: json-ld

Complete example
................
Description
,,,,,,,,,,,
This example covers all of the above cases, integrating all the annotations in the same document.

Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-complete.json
   :language: json-ld
