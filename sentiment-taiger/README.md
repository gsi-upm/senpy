# Senpy Plugin Taiger

Proxy for two of Taiger's sentiment analysis services for social media posts:

* taiger-plugin: proxy for a service that normalizes the text, and gives both a polarity and a polarity value for the text. It works for Spanish and English text.
* taiger3c-plugin: it uses a simpler service that only returns a polarity (positive, negative or none). It only works for Spanish.


## Usage

To use this plugin, you should use a GET Requests with the following possible params:
Params:	
- Input: text to analyse.(required)

## Example of Usage

Example request: 
```
curl http://senpy.cluster.gsi.dit.upm.es/api/?algo=sentiment-taiger&inputText=This%20is%20amazing

#Or, for the taiger3c plugin:
curl http://senpy.cluster.gsi.dit.upm.es/api/?algo=sentiment-taiger3c&inputText=Me%20encanta
```

This plugin follows the senpy schema and vocabularies, please visit [senpy documentation](http://senpy.readthedocs.io). Specifically, the NIF API section. 
It should look like this:

```
{
    "@context": "http://localhost:5005/api/contexts/Results.jsonld",
    "@id": "_:Results_1532449339.5887764",
    "@type": "results",
    "analysis": [
        "endpoint:plugins/sentiment-taiger_0.1"
    ],
    "entries": [
        {
            "@id": "#",
            "@type": "entry",
            "emotions": [],
            "entities": [],
            "nif:isString": "This is amazing",
            "sentiments": [
                {
                    "@id": "Opinion0",
                    "@type": "sentiment",
                    "marl:hasPolarity": "marl:Positive",
                    "marl:polarityValue": -1.4646806570973374,
                    "normalizedText": "This is amazing",
                    "prov:wasGeneratedBy": "endpoint:plugins/sentiment-taiger_0.1"
                }
            ],
            "suggestions": [],
            "topics": []
        }
    ]
}
```

As can be seen, this plugin analyzes sentiment giving three categories or tags: `marl:Positive`, `marl:Neutral` or `marl:Negative`, that will be held in the `marl:hasPolarity` field.
Moreover, the plugin retrieves a `marl:polarityValue` (a value between -1 and 1).
This plugin supports **python2.7** and **python3**.

![alt GSI Logo][logoGSI]

[logoGSI]: http://www.gsi.dit.upm.es/images/stories/logos/gsi.png "GSI Logo"

