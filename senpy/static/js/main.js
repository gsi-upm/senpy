var ONYX = "http://www.gsi.dit.upm.es/ontologies/onyx/ns#";
var RDF_TYPE =  "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
var plugins_params={};
function replaceURLWithHTMLLinks(text) {
    console.log('Text: ' + text);
    var exp = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    return text.replace(exp,'<a href="$1">$1</a>'); 
}

function encodeHTML(text) {
    return text.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;')
               .replace(/"/g, '&quot;')
               .replace(/'/g, '&apos;');
};

$(document).ready(function() {
    var response = JSON.parse($.ajax({type: "GET", url: "/api/plugins/" , async: false}).responseText);
    var defaultPlugin= JSON.parse($.ajax({type: "GET", url: "/api/default" , async: false}).responseText);
    html="";
    for (r in response){
      if (response[r]["name"]){
        if (response[r]["name"] == defaultPlugin["name"]){
          if (response[r]["is_activated"]){
            html+= "<option value=\""+response[r]["name"]+"\" selected=\"selected\">"+response[r]["name"]+"</option>"
          }else{
            html+= "<option value=\""+response[r]["name"]+"\" selected=\"selected\" disabled=\"disabled\">"+response[r]["name"]+"</option>"
          }
        }
        else{
          if (response[r]["is_activated"]){
            html+= "<option value=\""+response[r]["name"]+"\">"+response[r]["name"]+"</option>"
          }
          else{
            html+= "<option value=\""+response[r]["name"]+"\" disabled=\"disabled\">"+response[r]["name"]+"</option>"
          }
        }
      }
      if (response[r]["extra_params"]){
        plugins_params[response[r]["name"]]={};
        for (param in response[r]["extra_params"]){
          if (typeof response[r]["extra_params"][param] !="string"){
            var params = new Array();
            var alias = response[r]["extra_params"][param]["aliases"][0];
            params[alias]=new Array();
            for (option in response[r]["extra_params"][param]["options"]){
              params[alias].push(response[r]["extra_params"][param]["options"][option])
            }
            plugins_params[response[r]["name"]][alias] = (params[alias])
          }
        }
      }
    }
    document.getElementById('plugins').innerHTML = html;
    change_params();
});


function change_params(){
      var plugin = document.getElementById("plugins").options[document.getElementById("plugins").selectedIndex].value;

        for (param in plugins_params[plugin]){
          if (param || plugins_params[plugin][param].length > 1){
            html=""
            html+= "<label> Parameter "+param+"</label>"
            html+= "<select id=\""+param+"\" name=\""+param+"\">"
            for (option in plugins_params[plugin][param]){
                  html+="<option value \""+plugins_params[plugin][param][option]+"\">"+plugins_params[plugin][param][option]+"</option>"
            }
          }
          html+="</select>"
        }
        document.getElementById("params").innerHTML = html
};

function load_JSON(){
      url = "/api";
      var plugin = document.getElementById("plugins").options[document.getElementById("plugins").selectedIndex].value;
      var input = encodeURIComponent(document.getElementById("input").value);
      url += "?algo="+plugin+"&i="+input
      for (param in plugins_params[plugin]){
        if (param != null){
            var param_value = encodeURIComponent(document.getElementById(param).options[document.getElementById(param).selectedIndex].text);
            if (param_value){
              url+="&"+param+"="+param_value
            }
        }
      }
      var response = JSON.parse($.ajax({type: "GET", url: url , async: false}).responseText);
      document.getElementById("results").innerHTML = replaceURLWithHTMLLinks(JSON.stringify(response, undefined, 2))
      document.getElementById("input_request").innerHTML = "<label>"+url+"</label>"
  
}