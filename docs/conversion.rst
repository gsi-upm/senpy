Automatic Model Conversion
--------------------------

Senpy includes support for emotion and sentiment conversion.
When a user requests a specific model, senpy will choose a strategy to convert the model that the service usually outputs and the model requested by the user.

Out of the box, senpy can convert from the `emotionml:pad` (pleasure-arousal-dominance) dimensional model to `emoml:big6` (Ekman's big-6) categories, and vice versa.
This specific conversion uses a series of dimensional centroids (`emotionml:pad`) for each emotion category (`emotionml:big6`).
A dimensional value is converted to a category by looking for the nearest centroid.
The centroids are calculated according to this article:

.. code-block:: text

    Kim, S. M., Valitutti, A., & Calvo, R. A. (2010, June).
    Evaluation of unsupervised emotion models to textual affect recognition.
    In Proceedings of the NAACL HLT 2010 Workshop on Computational Approaches to Analysis and Generation of Emotion in Text (pp. 62-70).
    Association for Computational Linguistics.



It is possible to add new conversion strategies by `Developing a conversion plugin`_.


Use
===

Consider the following query to an emotion service:  http://senpy.gsi.upm.es/api/emotion-anew?i=good

The requested plugin (emotion-random) returns emotions using the VAD space (FSRE dimensions in EmotionML):

.. code:: json


   [
     {
       "@type": "EmotionSet",
       "onyx:hasEmotion": [
         {
           "@type": "Emotion",
           "emoml:pad-dimensions_arousal": 5.43,
           "emoml:pad-dimensions_dominance": 6.41,
           "emoml:pad-dimensions_pleasure": 7.47,
           "prov:wasGeneratedBy": "prefix:Analysis_1562744784.8789825"
         }
       ],
       "prov:wasGeneratedBy": "prefix:Analysis_1562744784.8789825"
     }
  ]
  

          

To get the equivalent of these emotions in Ekman's categories (i.e., Ekman's Big 6 in EmotionML), we'd do this:

http://senpy.gsi.upm.es/api/emotion-anew?i=good&emotion-model=emoml:big6

This call, provided there is a valid conversion plugin from Ekman's to VAD, would return something like this:

.. code:: json

   [
      {
        "@type": "EmotionSet",
        "onyx:hasEmotion": [
          {
            "@type": "Emotion",
            "onyx:algorithmConfidence": 4.4979,
            "onyx:hasEmotionCategory": "emoml:big6happiness"
          }
        ],
        "prov:wasDerivedFrom": {
          "@id": "Emotions0",
          "@type": "EmotionSet",
          "onyx:hasEmotion": [
            {
              "@id": "Emotion0",
              "@type": "Emotion",
              "emoml:pad-dimensions_arousal": 5.43,
              "emoml:pad-dimensions_dominance": 6.41,
              "emoml:pad-dimensions_pleasure": 7.47,
              "prov:wasGeneratedBy": "prefix:Analysis_1562745220.1553965"
            }
          ],
          "prov:wasGeneratedBy": "prefix:Analysis_1562745220.1553965"
        },
        "prov:wasGeneratedBy": "prefix:Analysis_1562745220.1570725"
      }
    ]


That is called a *full* response, as it simply adds the converted emotion alongside.
It is also possible to get the original emotion nested within the new converted emotion, using the `conversion=nested` parameter:

http://senpy.gsi.upm.es/api/emotion-anew?i=good&emotion-model=emoml:big6&conversion=nested

.. code:: json

   [
        {
          "@type": "EmotionSet",
          "onyx:hasEmotion": [
            {
              "@type": "Emotion",
              "onyx:algorithmConfidence": 4.4979,
              "onyx:hasEmotionCategory": "emoml:big6happiness"
            }
          ],
          "prov:wasDerivedFrom": {
            "@id": "Emotions0",
            "@type": "EmotionSet",
            "onyx:hasEmotion": [
              {
                "@id": "Emotion0",
                "@type": "Emotion",
                "emoml:pad-dimensions_arousal": 5.43,
                "emoml:pad-dimensions_dominance": 6.41,
                "emoml:pad-dimensions_pleasure": 7.47,
                "prov:wasGeneratedBy": "prefix:Analysis_1562744962.896306"
              }
            ],
            "prov:wasGeneratedBy": "prefix:Analysis_1562744962.896306"
          },
          "prov:wasGeneratedBy": "prefix:Analysis_1562744962.8978968"
        }
  ]



Lastly, `conversion=filtered` would only return the converted emotions.


.. code:: json

   [
      {
        "@type": "EmotionSet",
        "onyx:hasEmotion": [
          {
            "@type": "Emotion",
            "onyx:algorithmConfidence": 4.4979,
            "onyx:hasEmotionCategory": "emoml:big6happiness"
          }
        ],
        "prov:wasGeneratedBy": "prefix:Analysis_1562744925.7322266"
      }
   ]

Developing a conversion plugin
==============================

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


More implementation details are shown in the `centroids plugin <https://github.com/gsi-upm/senpy/blob/master/senpy/plugins/postprocessing/emotion/centroids.py>`_.
