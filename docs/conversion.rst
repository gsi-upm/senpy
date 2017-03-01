Conversion
----------

Senpy includes experimental support for emotion/sentiment conversion plugins.


Use
===

Consider the original query: http://127.0.0.1:5000/api/?i=hello&algo=emoRand

The requested plugin (emoRand) returns emotions using Ekman's model (or big6 in EmotionML):

.. code:: json


          ... rest of the document ...
          {
            "@type": "emotionSet",
            "onyx:hasEmotion": {
                "@type": "emotion",
                "onyx:hasEmotionCategory": "emoml:big6anger"
            },
            "prov:wasGeneratedBy": "plugins/emoRand_0.1"
          }

          

To get these emotions in VAD space (FSRE dimensions in EmotionML), we'd do this:

http://127.0.0.1:5000/api/?i=hello&algo=emoRand&emotionModel=emoml:fsre-dimensions

This call, provided there is a valid conversion plugin from Ekman's to VAD, would return something like this:

.. code:: json


          ... rest of the document ...
          {
            "@type": "emotionSet",
            "onyx:hasEmotion": {
                "@type": "emotion",
                "onyx:hasEmotionCategory": "emoml:big6anger"
                },
            "prov:wasGeneratedBy": "plugins/emoRand_0.1"
          }, {
            "@type": "emotionSet",
            "onyx:hasEmotion": {
                "@type": "emotion",
                "A": 7.22,
                "D": 6.28,
                "V": 8.6
            },
            "prov:wasGeneratedBy": "plugins/Ekman2VAD_0.1"

          }


That is called a *full* response, as it simply adds the converted emotion alongside.
It is also possible to get the original emotion nested within the new converted emotion, using the `conversion=nested` parameter:

.. code:: json


          ... rest of the document ...
          {
            "@type": "emotionSet",
            "onyx:hasEmotion": {
                "@type": "emotion",
                "onyx:hasEmotionCategory": "emoml:big6anger"
                },
            "prov:wasGeneratedBy": "plugins/emoRand_0.1"
            "onyx:wasDerivedFrom": {
                "@type": "emotionSet",
                "onyx:hasEmotion": {
                    "@type": "emotion",
                    "A": 7.22,
                    "D": 6.28,
                    "V": 8.6
                },
                "prov:wasGeneratedBy": "plugins/Ekman2VAD_0.1"
             }

          }


Lastly, `conversion=filtered` would only return the converted emotions.

Developing a conversion plugin
================================

Conversion plugins are discovered by the server just like any other plugin.
The difference is the slightly different API, and the need to specify the `source` and `target` of the conversion.
For instance, an emotion conversion plugin needs the following:


.. code:: yaml
          

          ---
          onyx:doesConversion:
            - onyx:conversionFrom: emoml:big6
              onyx:conversionTo: emoml:fsre-dimensions
            - onyx:conversionFrom: emoml:fsre-dimensions
              onyx:conversionTo: emoml:big6




.. code:: python


          class MyConversion(EmotionConversionPlugin):

              def convert(self, emotionSet, fromModel, toModel, params):
                  pass
