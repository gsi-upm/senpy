# Senpy Plugins


# Requirements

Some of these plugins require licensed files to run, such as lexicons or corpora.
You can **manually download these resources and add them to the `data` folder**.

Most plugins will look for these resources on activation.
By default, we set the flag `--allow-fail` in senpy, so if a plugin fails to activate, the server will still run with the remaining plugins.

# Running

## Using docker

To deploy all the plugins in this repository, run:

```
docker-compose up
```
A server should now be available at `http://localhost:5000`.

Alternatively, you can use docker manually with the version of senpy you wish:

```
docker run --rm -ti -p 5000:5000 -v $PWD:/senpy-plugins gsiupm/senpy:0.10.8-python2.7
```

Note that some versions are untested.

## Manually

First, install senpy from source or through pip:

```
pip install senpy
```

Now, you can try to run your plugins:

```
senpy -f .
```

Each plugin has different requirements.
Senpy will try its best to automatically install requirements (python libraries and NLTK resources) for each plugin.
Some cases may require manual installation of dependencies, or external packages.

# For developers / Contributors

## Licensed data

In our deployments, we keep all licensed data in a private submodule.
You will likely need to initialize this submodule if you're a contributor:

```
git submodule update --init --recursive 
```

## Adding a plugin from a separate repository

To add a plugin that has been developed in its own repository, you can use git-subtree as so:

```
$mname=<your plugin name>
$murl=<URL to your repository>

git remote add $mname $murl
git subtree add --prefix=$mname $mname master
```

Make sure to also add 

# LICENSE

This compilation of plugins for Senpy use Apache 2.0 License. Some of the resources used for train these plugins can not be distributed, specifically, resources for the plugins `emotion-anew` and `emotion-wnaffect`. For more information visit [Senpy documentation](senpy.readthedocs.io)
