# Senpy Plugin MeaningCloud

MeaningCloud plugin uses API from Meaning Cloud to perform sentiment analysis. 

For more information about Meaning Cloud and its services, please visit: https://www.meaningcloud.com/developer/apis

## Usage

To use this plugin, you need to obtain an API key from meaningCloud signing up here: https://www.meaningcloud.com/developer/login

When you had obtained the meaningCloud API Key, you have to provide it to the plugin, using the param **apiKey**.

Params:	
- Language: English (en) and Spanish (es)
- API Key: the API key from Meaning Cloud. Aliases: ["apiKey","meaningCloud-key"]
- Input: text to analyse.
- Model: model provided to Meaning Cloud API (for general domain)

## Example of Usage

Example requests: 
```
https://senpy.gsi.dit.upm.es/api/?algo=meaningCloud&language=en&apiKey=<put here your API key>&input=I%20love%20Madrid
```
