# Senpy Plugin MeaningCloud
	
	To use this plugin, you need to obtain an API_KEY from meaningCloud signing up here: https://www.meaningcloud.com/developer/login

Then run Senoy docker image with the path to this plugin as follows:
	
	```
    $ docker run -ti -p 5000:5000 -e DAEDALUS_KEY=02079c6e4e97d85f3fa483cd42180042 -v $PWD:/plugins gsiupm/senpy --host 0.0.0.0 -f /plugins
    ```