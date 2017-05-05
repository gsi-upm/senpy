# Plugin emotion-anew 

This plugin consists on an **emotion classifier** that detects six possible emotions:
- Anger : general-dislike.
- Fear : negative-fear.
- Disgust : shame.
- Joy : gratitude, affective, enthusiasm, love, joy, liking.
- Sadness : ingrattitude, daze, humlity, compassion, despair, anxiety, sadness.
- Neutral: not detected a particulary emotion. 

The plugin uses **ANEW lexicon** dictionary to calculate VAD (valence-arousal-dominance) of the sentence and determinate which emotion is closer to this value. To do this comparision, it is defined that each emotion has a centroid, calculated according to this article: http://www.aclweb.org/anthology/W10-0208. 

The plugin is going to look for the words in the sentence that appear in the ANEW dictionary and calculate the average VAD score for the sentence. Once this score is calculated, it is going to seek the emotion that is closest to this value.

The response of this plugin uses [Onyx ontology](https://www.gsi.dit.upm.es/ontologies/onyx/) developed at GSI UPM, to express the information.

##Usage

Params accepted:
- Language: English (en) and Spanish (es).
- Input: input text to analyse.


Example request: 
```
http://senpy.cluster.gsi.dit.upm.es/api/?algo=emotion-anew&language=en&input=I%20love%20Madrid
```

Example respond: This plugin follows the standard for the senpy plugin response. For more information, please visit [senpy documentation](http://senpy.readthedocs.io). Specifically, NIF API section.
# Known issues

- To obtain Anew dictionary you can download from here: <https://github.com/hcorona/SMC2015/blob/master/resources/ANEW2010All.txt> 



![alt GSI Logo][logoGSI]

[logoES]: https://www.gsi.dit.upm.es/ontologies/onyx/img/eurosentiment_logo.png "EuroSentiment logo"
[logoGSI]: http://www.gsi.dit.upm.es/images/stories/logos/gsi.png "GSI Logo"
