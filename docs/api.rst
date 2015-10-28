NIF API
=======
.. http:get:: /api

   Basic endpoint for sentiment/emotion analysis.

   **Example request**:

   .. sourcecode:: http

      GET /api?input=I%20love%20GSI HTTP/1.1
      Host: localhost
      Accept: application/json, text/javascript


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: text/javascript

      {
        "@context": [
          "http://127.0.0.1/static/context.jsonld",
      ],
      "analysis": [
        {
          "@id": "SentimentAnalysisExample",
          "@type": "marl:SentimentAnalysis",
          "dc:language": "en", 
          "marl:maxPolarityValue": 10.0,
          "marl:minPolarityValue": 0.0
        }
      ],
      "domain": "wndomains:electronics", 
      "entries": [
        {
          "opinions": [
            {
              "prov:generatedBy": "SentimentAnalysisExample",
              "marl:polarityValue": 7.8, 
              "marl:hasPolarity": "marl:Positive",
              "marl:describesObject": "http://www.gsi.dit.upm.es",
            }
          ],
          "nif:isString": "I love GSI",
          "strings": [
            {
              "nif:anchorOf": "GSI",
              "nif:taIdentRef": "http://www.gsi.dit.upm.es"
            }
          ]
        }
       ]
      }

   :query i input: No default. Depends on informat and intype
   :query f informat: one of `turtle` (default), `text`, `json-ld`
   :query t intype: one of `direct` (default), `url`
   :query o outformat: one of `turtle` (default), `text`, `json-ld`
   :query p prefix: prefix for the URIs
   :query algo algorithm: algorithm/plugin to use for the analysis. For a list of options, see :http:get:`/api/plugins`. If not provided, the default plugin will be used (:http:get:`/api/plugins/default`).

   :reqheader Accept: the response content type depends on
                      :mailheader:`Accept` header
   :resheader Content-Type: this depends on :mailheader:`Accept`
                            header of request
   :statuscode 200: no error
   :statuscode 404: service not found

.. http:post:: /api

   The same as :http:get:`/api`.

.. http:get:: /api/plugins

   Returns a list of installed plugins. 
   **Example request**:

   .. sourcecode:: http

      GET /api/plugins HTTP/1.1
      Host: localhost
      Accept: application/json, text/javascript


   **Example response**:

   .. sourcecode:: http

        {
            "@context": {
                   ...
            }, 
            "sentiment140": {
                "name": "sentiment140", 
                "is_activated": true, 
                "version": "0.1", 
                "extra_params": {
                    "@id": "extra_params_sentiment140_0.1", 
                    "language": {
                        "required": false, 
                        "@id": "lang_sentiment140", 
                        "options": [
                            "es", 
                            "en", 
                            "auto"
                        ], 
                        "aliases": [
                            "language", 
                            "l"
                        ]
                    }
                }, 
                "@id": "sentiment140_0.1"
            }, 
            "rand": {
                "name": "rand", 
                "is_activated": true, 
                "version": "0.1", 
                "extra_params": {
                    "@id": "extra_params_rand_0.1", 
                    "language": {
                        "required": false, 
                        "@id": "lang_rand", 
                        "options": [
                            "es", 
                            "en", 
                            "auto"
                        ], 
                        "aliases": [
                            "language", 
                            "l"
                        ]
                    }
                }, 
                "@id": "rand_0.1"
            }
        }


.. http:get:: /api/plugins/<pluginname>

   Returns the information of a specific plugin.
   **Example request**:

   .. sourcecode:: http

      GET /api/plugins/rand HTTP/1.1
      Host: localhost
      Accept: application/json, text/javascript


   **Example response**:

   .. sourcecode:: http

      {
          "@id": "rand_0.1",
          "extra_params": {
              "@id": "extra_params_rand_0.1",
              "language": {
                  "@id": "lang_rand",
                  "aliases": [
                      "language",
                      "l"
                  ],
                  "options": [
                      "es",
                      "en",
                      "auto"
                  ],
                  "required": false
              }
          },
          "is_activated": true,
          "name": "rand",
          "version": "0.1"
      }


.. http:get:: /api/plugins/default

   Return the information about the default plugin.

.. http:get:: /api/plugins/<pluginname>/{de}activate

   {De}activate a plugin.

   **Example request**:

   .. sourcecode:: http

      GET /api/plugins/rand/deactivate HTTP/1.1
      Host: localhost
      Accept: application/json, text/javascript


   **Example response**:

   .. sourcecode:: http

       {
          "@context": {}, 
          "message": "Ok"
       }
