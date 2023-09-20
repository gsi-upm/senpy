# Sentimet-vader plugin

Vader is a plugin developed at GSI UPM for sentiment analysis.  
The response of this plugin uses [Marl ontology](https://www.gsi.dit.upm.es/ontologies/marl/) developed at GSI UPM for semantic web.

## Acknowledgements

This plugin uses the vaderSentiment module underneath, which is described in the paper:

  VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text
  C.J. Hutto and Eric Gilbert
  Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.

If you use this plugin in your research, please cite the above paper.

For more information about the functionality, check the official repository

https://github.com/cjhutto/vaderSentiment

## Usage

Parameters:

- Language: es (Spanish), en(English).
- Input: Text to analyse.


Example request: 

```
http://senpy.cluster.gsi.dit.upm.es/api/?algo=sentiment-vader&language=en&input=I%20love%20Madrid
```

Example respond: This plugin follows the standard for the senpy plugin response. For more information, please visit [senpy documentation](http://senpy.readthedocs.io). Specifically, NIF API section. 

This plugin supports **python3**

![alt GSI Logo][logoGSI]

[logoGSI]: http://www.gsi.dit.upm.es/images/stories/logos/gsi.png "GSI Logo"

========
