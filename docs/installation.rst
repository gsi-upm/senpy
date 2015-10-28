Installation
------------
The stable version can be installed in three ways.

Through PIP
***********

.. code:: bash

   pip install --user senpy

   
Alternatively, you can use the development version:
 
.. code:: bash

   git clone git@github.com:gsi-upm/senpy
   cd senpy
   pip install --user .

If you want to install senpy globally, use sudo instead of the ``--user`` flag.

Docker Image
************
Build the image or use the pre-built one: ``docker run -ti -p 5000:5000 balkian/senpy --host 0.0.0.0 --default-plugins``.

To add custom plugins, add a volume and tell senpy where to find the plugins: ``docker run -ti -p 5000:5000 -v <PATH OF PLUGINS>:/plugins balkian/senpy --host 0.0.0.0 --default-plugins -f /plugins``
