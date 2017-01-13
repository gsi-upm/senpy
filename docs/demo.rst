Demo
----

There is a demo available on http://senpy.cluster.gsi.dit.upm.es/, where you can a serie of different plugins. You can use them in the playground or make a directly requests to the service.

.. image:: senpy-playground.png
  :height: 400px
  :width: 800px
  :scale: 100 %
  :align: center

Plugins Demo
============

The next plugins are available at the demo:

* emoTextAnew extracts the VAD (valence-arousal-dominance) of a sentence by matching words from the ANEW dictionary.
* emoTextWordnetAffect based on the hierarchy of WordnetAffect to calculate the emotion of the sentence.
* vaderSentiment utilizes the software from vaderSentiment to calculate the sentiment of a sentence.
* sentiText is a software developed during the TASS 2015 competition, it has been adapted for English and Spanish.

emoTextANEW plugin
******************

This plugin is going to used the ANEW lexicon dictionary to calculate de VAD (valence-arousal-dominance) of the sentence and the determinate which emotion is closer to this value.

Each emotion has a centroid, which it has been approximated using the formula described in this article:

http://www.aclweb.org/anthology/W10-0208

The plugin is going to look for the words in the sentence that appear in the ANEW dictionary and calculate the average VAD score for the sentence. Once this score is calculated, it is going to seek the emotion that is closest to this value.

emoTextWAF plugin
*****************

This plugin uses WordNet-Affect (http://wndomains.fbk.eu/wnaffect.html) to calculate the percentage of each emotion. The emotions that are going to be used are: anger, fear, disgust, joy and sadness. It is has been used a emotion mapping enlarge the emotions:

* anger : general-dislike
* fear : negative-fear
* disgust : shame
* joy : gratitude, affective, enthusiasm, love, joy, liking
* sadness : ingrattitude, daze, humlity, compassion, despair, anxiety, sadness

sentiText plugin
****************

This plugin is based in the classifier developed for the TASS 2015 competition. It has been developed for Spanish and English. The different phases that has this plugin when it is activated:

* Train both classifiers (English and Spanish).
* Initialize resources (dictionaries,stopwords,etc.).
* Extract bag of words,lemmas and chars.

Once the plugin is activated, the features that are going to be extracted for the classifiers are:

* Matches with the bag of words extracted from the train corpus.
* Sentiment score of the sentences extracted from the dictionaries (lexicons and emoticons).
* Identify negations and intensifiers in the sentences.
* Complementary features such as exclamation and interrogation marks, eloganted and caps words, hashtags, etc.

The plugin has a preprocessor, which is focues on Twitter corpora, that is going to be used for cleaning the text to simplify the feature extraction.

There is more information avaliable in the next article.

Aspect based Sentiment Analysis of Spanish Tweets, Oscar Araque and Ignacio Corcuera-Platas and Constantino Román-Gómez and Carlos A. Iglesias and J. Fernando Sánchez-Rada. http://gsi.dit.upm.es/es/investigacion/publicaciones?view=publication&task=show&id=37

vaderSentiment plugin
*********************

For developing this plugin, it has been used the module vaderSentiment, which is described in the paper: VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text C.J. Hutto and Eric Gilbert Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.

If you use this plugin in your research, please cite the above paper

For more information about the functionality, check the official repository

https://github.com/cjhutto/vaderSentiment
