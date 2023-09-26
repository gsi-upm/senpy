# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
* The code of many senpy community plugins have been included by default. However, additional files (e.g., licensed data) and/or installing additional dependencies may be necessary for some plugins. Read each plugin's documentation for more information.
* `--strict` flag, to fail and not start when a 
* `optional` attribute in plugins. Optional plugins may fail to load or activate but the server will be started regardless, unless running in strict mode
* Option in shelf plugins to ignore pickling errors
### Removed
* `--only-install`, `--only-test` and `--only-list` flags were removed in favor of `--no-run` + `--install`/`--test`/`--dependencies`
### Changed
* data directory selection logic is slightly modified, and will choose one of the following (in this order): `data_folder` (argument), `$SENPY_DATA` or `$CWD`

## [1.0.6]
### Fixed
* Plugins now get activated for testing
## [1.0.1]
### Added
* License headers
* Description for PyPI (setup.py)

### Changed
* The evaluation tab shows datasets inline, and a tooltip shows the number of instances
* The docs should be clearer now

## [1.0.0]
### Fixed
* Restored hash changing function in `main.js`

## 0.20

### Added
* Objects can control the keys that will be used in `serialize`/`jsonld`/`as_dict` by specifying a list of keys in `terse_keys`.
e.g.
```python
>>> class MyModel(senpy.models.BaseModel):
...   _terse_keys = ['visible']
...   invisible = 5
...   visible = 1
...
>>> m = MyModel(id='testing')
>>> m.jsonld()
{'invisible': 5, 'visible': 1, '@id': 'testing'}
>>> m.jsonld(verbose=False)
{'visible': 1}
```
* Configurable logging format.
* Added default terse keys for the most common classes (entry, sentiment, emotion...).
* Flag parameters (boolean) are set to true even when no value is added (e.g. `&verbose` is the same as `&verbose=true`).
* Plugin and parameter descriptions are now formatted with (showdown)[https://github.com/showdownjs/showdown].
* The web UI requests extra_parameters from the server. This is useful for pipelines. See #52
* First batch of semantic tests (using SPARQL)
* `Plugin.path()` method to get a file path from a relative path (using the senpy data folder)

### Changed
* `install_deps` now checks what requirements are already met before installing with pip.
* Help is now provided verbosely by default
* Other outputs are terse by default. This means some properties are now hidden unless verbose is set.
* `sentiments` and `emotions` are now `marl:hasOpinion` and `onyx:hasEmotionSet`, respectively.
* Nicer logging format
* Context aliases (e.g. `sentiments` and `emotions` properties) have been replaced with the original properties (e.g. `marl:hasOpinion` and `onyx:hasEmotionSet**), to use aliases, pass the `aliases** parameter.
* Several UI improvements
  * Dedicated tab to show the list of plugins
  * URLs in plugin descriptions are shown as links
  * The format of the response is selected by clicking on a tab instead of selecting from a drop-down
  * list of examples
  * Bootstrap v4
* RandEmotion and RandSentiment are no longer included in the base set of plugins
* The `--plugin-folder` option can be used more than once, and every folder will be added to the app.

### Deprecated
### Removed
* Python 2.7 is no longer test or officially supported
### Fixed
* Plugin descriptions are now dedented when they are extracted from the docstring.
### Security

