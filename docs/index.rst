Welcome to Senpy's documentation!
=================================

.. image:: https://readthedocs.org/projects/senpy/badge/?version=latest
  :target: http://senpy.readthedocs.io/en/latest/
.. image:: https://badge.fury.io/py/senpy.svg
  :target: https://badge.fury.io/py/senpy
.. image:: https://lab.gsi.upm.es/senpy/senpy/badges/master/build.svg
  :target: https://lab.gsi.upm.es/senpy/senpy/commits/master
.. image:: https://lab.gsi.upm.es/senpy/senpy/badges/master/coverage.svg
  :target: https://lab.gsi.upm.es/senpy/senpy/commits/master
.. image:: https://img.shields.io/pypi/l/requests.svg
  :target: https://lab.gsi.upm.es/senpy/senpy/

Senpy is a framework to build sentiment and emotion analysis services.
It provides functionalities for:

- developing sentiment and emotion classifier and exposing them as an HTTP service
- requesting sentiment and emotion analysis from different providers (i.e. Vader, Sentimet140, ...) using the same interface (:doc:`apischema`). In this way, applications do not depend on the API offered for these services.
- combining services that use different sentiment model (e.g. polarity between [-1, 1] or [0,1] or emotion models (e.g. Ekkman or VAD)
- evaluating sentiment algorithms with well known datasets


Using senpy services is as simple as sending an HTTP request with your favourite tool or library.
Let's analyze the sentiment of the text "Senpy is awesome".

We can call the `Sentiment140 <http://www.sentiment140.com/>`_ service with an HTTP request using curl:


.. code:: shell
   :emphasize-lines: 14,18

   $ curl "http://senpy.gsi.upm.es/api/sentiment140" \
         --data-urlencode "input=Senpy is awesome"

   {
     "@context": "http://senpy.gsi.upm.es/api/contexts/YXBpL3NlbnRpbWVudDE0MD8j",
     "@type": "Results",
     "entries": [
       {
         "@id": "prefix:",
         "@type": "Entry",
         "marl:hasOpinion": [
           {
             "@type": "Sentiment",
             "marl:hasPolarity": "marl:Positive",
             "prov:wasGeneratedBy": "prefix:Analysis_1554389334.6431913"
           }
         ],
         "nif:isString": "Senpy is awesome",
         "onyx:hasEmotionSet": []
       }
     ]
   }


Congratulations, you’ve used your first senpy service!
You can observe the result: the polarity is positive (marl:Positive). The reason of this prefix is that Senpy follows a linked data approach.

You can analyze the same sentence using a different sentiment service (e.g. Vader) and requesting a different format (e.g. turtle):



.. code:: shell

   $ curl "http://senpy.gsi.upm.es/api/sentiment-vader" \
         --data-urlencode "input=Senpy is awesome" \
         --data-urlencode "outformat=turtle"

   @prefix : <http://www.gsi.upm.es/onto/senpy/ns#> .
   @prefix endpoint: <http://senpy.gsi.upm.es/api/> .
   @prefix marl: <http://www.gsi.dit.upm.es/ontologies/marl/ns#> .
   @prefix nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .
   @prefix prefix: <http://senpy.invalid/> .
   @prefix prov: <http://www.w3.org/ns/prov#> .
   @prefix senpy: <http://www.gsi.upm.es/onto/senpy/ns#> .

   prefix: a senpy:Entry ;
       nif:isString "Senpy is awesome" ;
       marl:hasOpinion [ a senpy:Sentiment ;
               marl:hasPolarity "marl:Positive" ;
               marl:polarityValue 6.72e-01 ;
               prov:wasGeneratedBy prefix:Analysis_1562668175.9808676 ] .

   [] a senpy:Results ;
       prov:used prefix: .

As you see, Vader returns also the polarity value (0.67) in addition to the category (positive).

If you are interested in consuming Senpy services, read :doc:`Quickstart`.
To get familiar with the concepts behind Senpy, and what it can offer for service developers, check out :doc:`development`.
:doc:`apischema` contains information about the semantic models and vocabularies used by Senpy.

.. toctree::
  :caption: Learn more about senpy:
  :maxdepth: 2
  :hidden:

  senpy
  demo
  Quickstart.ipynb
  installation
  conversion
  Evaluation.ipynb
  apischema
  development
  publications
  projects
