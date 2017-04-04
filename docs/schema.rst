Schema
------
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

Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-sentiment.json
   :emphasize-lines: 5-10,25-33
   :language: json-ld

Suggestion Mining
.................
Description
,,,,,,,,,,,

Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-suggestion.json
   :emphasize-lines: 5-8,22-27
   :language: json-ld

Emotion Analysis
................
Description
,,,,,,,,,,,

Representation
,,,,,,,,,,,,,,

.. literalinclude:: examples/results/example-emotion.json
   :language: json-ld
   :emphasize-lines: 5-8,25-37

Named Entity Recognition
........................
Description
,,,,,,,,,,,

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
