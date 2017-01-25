# Senpy Plugin MeaningCloud

MeaningCloud plugin uses API from Meaning Cloud to perform sentiment analysis. 

For more information about Meaning Cloud and its services, please visit: https://www.meaningcloud.com/developer/apis

## Usage

To use this plugin, you need to obtain an API key from meaningCloud signing up here: https://www.meaningcloud.com/developer/login

When you had obtained the meaningCloud API Key, you have to provide it to the plugin, using the param **apiKey**.

To use this plugin, you should use a GET Requests with the following possible params:
Params:	
- Language: English (en) and Spanish (es). (default: en)
- API Key: the API key from Meaning Cloud. Aliases: ["apiKey","meaningCloud-key"]. (required)
- Input: text to analyse.(required)
- Model: model provided to Meaning Cloud API (for general domain). (default: general)

## Example of Usage

Example request: 
```
http://senpy.cluster.gsi.dit.upm.es/api/?algo=meaningCloud&language=en&apiKey=<put here your API key>&input=I%20love%20Madrid
```


Example respond: This plugin follows the standard for the senpy plugin response. For more information, please visit [senpy documentation](http://senpy.readthedocs.io). Specifically, NIF API section. 

![alt GSI Logo][logoGSI]

[logoGSI]: http://www.gsi.dit.upm.es/images/stories/logos/gsi.png "GSI Logo"
