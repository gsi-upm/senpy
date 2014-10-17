'''
SENTIMENT140
=============

* http://www.sentiment140.com/api/bulkClassifyJson
* Method: POST
* Parameters: JSON Object (that is copied to the result)
    * text
    * query
    * language
    * topic

* Example response:
```json
{"data": [{"text": "I love Titanic.", "id":1234, "polarity": 4},
          {"text": "I hate Titanic.", "id":4567, "polarity": 0}]}
```
'''
import requests
import json

ENDPOINT_URI = "http://www.sentiment140.com/api/bulkClassifyJson"

def analyse(texts):
    parameters = {"data": []}
    if isinstance(texts, list):
        for text in texts:
            parameters["data"].append({"text": text})
    else:
        parameters["data"].append({"text": texts})

    res = requests.post(ENDPOINT_URI, json.dumps(parameters))
    res.json()
    return res.json()

def test():
    print analyse("I love Titanic")
    print analyse(["I love Titanic", "I hate Titanic"])

if __name__ == "__main__":
    test()
