# Sentiment basic plugin

This plugin is based on the classifier developed for the TASS 2015 competition. It has been developed for Spanish and English. This is a demo plugin that uses only some features from the TASS 2015 classifier. To use the entirely functional classifier you can use the service in: http://senpy.cluster.gsi.dit.upm.es

There is more information avaliable in:
	
	- Aspect based Sentiment Analysis of Spanish Tweets, Oscar Araque and Ignacio Corcuera-Platas and Constantino Román-Gómez and Carlos A. Iglesias and J. Fernando Sánchez-Rada. http://gsi.dit.upm.es/es/investigacion/publicaciones?view=publication&task=show&id=376

## Usage
Params accepted:

- Language: Spanish (es).
- Input: text to analyse.


Example request: 
```
http://senpy.cluster.gsi.dit.upm.es/api/?algo=sentiment-basic&language=es&input=I%20love%20Madrid
```

Example respond: This plugin follows the standard for the senpy plugin response. For more information, please visit [senpy documentation](http://senpy.readthedocs.io). Specifically, NIF API section. 

This plugin only supports **python2**


![alt GSI Logo][logoGSI]

[logoGSI]: http://www.gsi.dit.upm.es/images/stories/logos/gsi.png "GSI Logo"
