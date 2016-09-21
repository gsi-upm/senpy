This plugin uses WNAffect labels for emotion analysis.

The emotextWAF.senpy file can be copied and modified to use different versions of wnaffect with the same python code.


Known issues
============

  * This plugin uses the pattern library, which means it will only run on python 2.7
  * Wnaffect and corpora files are not included in the repository, but can be easily added either to the docker image (using a volume) or in a new docker image.
