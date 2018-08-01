# Senpy Plugin Taiger

Service that analyzes sentiments from social posts written in Spanish or English.


## Usage

To use this plugin, you should use a GET Requests with the following possible params:
Params:	
- Input: text to analyse.(required)
- Endpoint: Enpoint to the Taiger service.

## Example of Usage

Example request: 
```
http://senpy.cluster.gsi.dit.upm.es/api/?algo=sentiment-taiger&inputText=This%20is%20amazing
```

Example respond: This plugin follows the standard for the senpy plugin response. For more information, please visit [senpy documentation](http://senpy.readthedocs.io). Specifically, NIF API section. 

For example, this would be the example respond for the request done.

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

As it can be seen, this plugin analyzes sentiment givin three categories or tags: `marl:Positive`, `marl:Neutral` or `marl:Negative`, that will be held in the `marl:hasPolarity` field. Moreover, the plugin retrieves a `marl:polarityValue`.
This plugin supports **python2.7** and **python3**.

![alt GSI Logo][logoGSI]

[logoGSI]: http://www.gsi.dit.upm.es/images/stories/logos/gsi.png "GSI Logo"

