# WordNet-Affect plugin

This plugin uses WordNet-Affect (http://wndomains.fbk.eu/wnaffect.html) to calculate the percentage of each emotion. The plugin classifies among five diferent emotions: anger, fear, disgust, joy and sadness. It is has been used a emotion mapping enlarge the emotions:

- anger : general-dislike
- fear : negative-fear
- disgust : shame
- joy : gratitude, affective, enthusiasm, love, joy, liking
- sadness : ingrattitude, daze, humlity, compassion, despair, anxiety, sadness

## Installation

* Download
```
git clone https://lab.cluster.gsi.dit.upm.es/senpy/emotion-wnaffect.git
```
* Get data
```
cd emotion-wnaffect
git submodule update --init --recursive
```
* Run 
```
docker run -p 5000:5000 -v $PWD:/plugins gsiupm/senpy -f /plugins
```

## Data format

`data/a-hierarchy.xml` is a xml file
`data/a-synsets.xml` is a xml file

## Usage

The parameters accepted are:

- Language: English (en).
- Input: Text to analyse.

Example request: 
```
http://senpy.cluster.gsi.dit.upm.es/api/?algo=emotion-wnaffect&language=en&input=I%20love%20Madrid
```

Example respond: This plugin follows the standard for the senpy plugin response. For more information, please visit [senpy documentation](http://senpy.readthedocs.io). Specifically, NIF API section. 


The response of this plugin uses [Onyx ontology](https://www.gsi.dit.upm.es/ontologies/onyx/) developed at GSI UPM for semantic web.

This plugin uses WNAffect labels for emotion analysis.

The emotion-wnaffect.senpy file can be copied and modified to use different versions of wnaffect with the same python code.


## Known issues

-  This plugin run on **Python2.7** and **Python3.5**
-  Wnaffect and corpora files are not included in the repository, but can be easily added either to the docker image (using a volume) or in a new docker image. 
-  You can download Wordnet 1.6 here: <http://wordnetcode.princeton.edu/1.6/wn16.unix.tar.gz> and extract the dict folder. 
-  The hierarchy and synsets files can be found here: <https://github.com/larsmans/wordnet-domains-sentiwords/tree/master/wn-domains/wn-affect-1.1>

![alt GSI Logo][logoGSI]
[logoGSI]: http://www.gsi.dit.upm.es/images/stories/logos/gsi.png "GSI Logo"
