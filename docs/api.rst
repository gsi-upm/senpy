NIF API
-------
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
        "@context":"http://127.0.0.1/api/contexts/Results.jsonld",
        "@id":"_:Results_11241245.22",
        "@type":"results"
        "activities": [
          "plugins/sentiment-140_0.1" 
        ],
        "entries": [
          {  
            "@id": "_:Entry_11241245.22"
            "@type":"entry",
            "emotions": [],
            "entities": [],
            "sentiments": [
              {  
                "@id": "Sentiment0",  
                "@type": "sentiment", 
                "marl:hasPolarity": "marl:Negative",
                "marl:polarityValue": 0,
                "prefix": ""
              }
            ],
            "suggestions": [],
            "text": "This text makes me sad.\nwhilst this text makes me happy and surprised at the same time.\nI cannot believe it!",
            "topics": []
          }
        ]
      }

   :query i input: No default. Depends on informat and intype
   :query f informat: one of `turtle` (default), `text`, `json-ld`
   :query t intype: one of `direct` (default), `url`
   :query o outformat: one of `turtle` (default), `text`, `json-ld`
   :query p prefix: prefix for the URIs
   :query algo algorithm: algorithm/plugin to use for the analysis. For a list of options, see :http:get:`/api/plugins`. If not provided, the default plugin will be used (:http:get:`/api/plugins/default`).
   :query algo emotionModel: desired emotion model in the results. If the requested algorithm does not use that emotion model, there are conversion plugins specifically for this. If none of the plugins match, an error will be returned, which includes the results *as is*.

   :reqheader Accept: the response content type depends on
                      :mailheader:`Accept` header
   :resheader Content-Type: this depends on :mailheader:`Accept`
                            header of request
   :statuscode 200: no error
   :statuscode 404: service not found
   :statuscode 400: error while processing the request

.. http:post:: /api

   The same as :http:get:`/api`.

.. http:get:: /api/plugins

   Returns a list of installed plugins. 
   **Example request and response**:

   .. sourcecode:: http

      GET /api/plugins HTTP/1.1
      Host: localhost
      Accept: application/json, text/javascript


      {
        "@id": "plugins/sentiment-140_0.1", 
        "@type": "sentimentPlugin", 
        "author": "@balkian", 
        "description": "Sentiment classifier using rule-based classification for English and Spanish. This plugin uses sentiment140 data to perform classification. For more information: http://help.sentiment140.com/for-students/", 
        "extra_params": {
          "language": {
            "@id": "lang_sentiment140", 
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
        "maxPolarityValue": 1.0, 
        "minPolarityValue": 0.0, 
        "module": "sentiment-140", 
        "name": "sentiment-140", 
        "requirements": {}, 
        "version": "0.1"
      }, 
      {
        "@id": "plugins/ExamplePlugin_0.1", 
        "@type": "sentimentPlugin", 
        "author": "@balkian", 
        "custom_attribute": "42", 
        "description": "I am just an example", 
        "extra_params": {
          "parameter": {
            "@id": "parameter", 
            "aliases": [
              "parameter", 
              "param"
            ], 
            "default": 42, 
            "required": true
          }
        }, 
        "is_activated": true, 
        "maxPolarityValue": 1.0, 
        "minPolarityValue": 0.0, 
        "module": "example", 
        "name": "ExamplePlugin", 
        "requirements": "noop", 
        "version": "0.1"
      }

.. http:get:: /api/plugins/<pluginname>

   Returns the information of a specific plugin.
   **Example request and response**:

   .. sourcecode:: http

      GET /api/plugins/sentiment-random/ HTTP/1.1
      Host: localhost
      Accept: application/json, text/javascript

      {
        "@context": "http://127.0.0.1/api/contexts/ExamplePlugin.jsonld", 
        "@id": "plugins/ExamplePlugin_0.1", 
        "@type": "sentimentPlugin", 
        "author": "@balkian", 
        "custom_attribute": "42", 
        "description": "I am just an example", 
        "extra_params": {
          "parameter": {
            "@id": "parameter", 
            "aliases": [
              "parameter", 
              "param"
            ], 
            "default": 42, 
            "required": true
          }
        }, 
        "is_activated": true, 
        "maxPolarityValue": 1.0, 
        "minPolarityValue": 0.0, 
        "module": "example", 
        "name": "ExamplePlugin", 
        "requirements": "noop", 
        "version": "0.1"
      }





























.. http:get:: /api/plugins/default

   Return the information about the default plugin.

