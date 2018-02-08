# Senpy Plugins

# Installing


First, install senpy from source or through pip:

    pip install senpy

Each plugin has different requirements.
As of this writing, requirement installation is done manually for each plugin.
All requirements are specified in the .senpy file and, alternatively, in a requirements.txt file.

# Running

Run with:

    git clone https://github.com/gsi-upm/senpy-plugins-community.git
    senpy -f senpy-plugins-community
# Loading new plugins to gitlab

You should have two repos, one with data files and the main repo of the plugin. 
First you have to push all the data files in the data repo and the code of the plugin in the main repo. Next, you have to "link" the two repos using submodule:

    git submodule add ../data/<NAME OF YOUR PLUGIN> ./data

# LICENSE

This compilation of plugins for Senpy use Apache 2.0 License. Some of the resources used for train these plugins can not be distributed, specifically, resources for the plugins `emotion-anew` and `emotion-wnaffect`. For more information visit [Senpy documentation](senpy.readthedocs.io)
