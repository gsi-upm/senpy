Installation
------------
The stable version can be used in two ways: as a system/user library through pip, or from a docker image.

Using docker is recommended because the image is self-contained, reproducible and isolated from the system, which means:

  * It can be downloaded and run with just one simple command
  * All dependencies are included
  * It is OS-independent (MacOS, Windows, GNU/Linux)
  * Several versions may coexist in the same machine without additional virtual environments

Additionally, you may create your own docker image with your custom plugins, ready to be used by others.


Through PIP
***********

.. code:: bash

   pip install senpy

   # Or with --user if you get permission errors:

   pip install --user senpy
   
..
   Alternatively, you can use the development version:

   .. code:: bash

      git clone git@github.com:gsi-upm/senpy
      cd senpy
      pip install --user .

Each version is automatically tested in GNU/Linux, macOS and Windows 10.
If you have trouble with the installation, please file an `issue on GitHub <https://github.com/gsi-upm/senpy/issues>`_.


Docker Image
************

The base image of senpy comes with some built-in plugins that you can use:   

.. code:: bash

   docker run -ti -p 5000:5000 gsiupm/senpy --host 0.0.0.0

To use your custom plugins, you can add volume to the container: 
    
.. code:: bash

   docker run -ti -p 5000:5000 -v <PATH OF PLUGINS>:/plugins gsiupm/senpy --host 0.0.0.0 --plugins -f /plugins


Alias
.....

If you are using the docker approach regularly, it is advisable to use a script or an alias to simplify your executions:

.. code:: bash

   alias senpy='docker run --rm -ti -p 5000:5000 -v $PWD:/senpy-plugins gsiupm/senpy'


Now, you may run senpy from any folder in your computer like so:

.. code:: bash

   senpy --version
