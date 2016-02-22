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

function hashchanged(){
    var hash = location.hash
          , hashPieces = hash.split('?');
    if( hashPieces[0].length > 0 ){
        activeTab = $('[href=' + hashPieces[0] + ']');
        activeTab && activeTab.tab('show');
    }
}

$(document).ready(function() {
    var response = JSON.parse($.ajax({type: "GET", url: "/api/plugins/" , async: false}).responseText);
    var defaultPlugin= JSON.parse($.ajax({type: "GET", url: "/api/plugins/default" , async: false}).responseText);
    html="";
    plugins = response.plugins;
    for (r in plugins){
      if (plugins[r]["name"]){
        if (plugins[r]["name"] == defaultPlugin["name"]){
          if (plugins[r]["is_activated"]){
            html+= "<option value=\""+plugins[r]["name"]+"\" selected=\"selected\">"+plugins[r]["name"]+"</option>"
          }else{
            html+= "<option value=\""+plugins[r]["name"]+"\" selected=\"selected\" disabled=\"disabled\">"+plugins[r]["name"]+"</option>"
          }
        }
        else{
          if (plugins[r]["is_activated"]){
            html+= "<option value=\""+plugins[r]["name"]+"\">"+plugins[r]["name"]+"</option>"
          }
          else{
            html+= "<option value=\""+plugins[r]["name"]+"\" disabled=\"disabled\">"+plugins[r]["name"]+"</option>"
          }
        }
      }
      if (plugins[r]["extra_params"]){
        plugins_params[plugins[r]["name"]]={};
        for (param in plugins[r]["extra_params"]){
          if (typeof plugins[r]["extra_params"][param] !="string"){
            var params = new Array();
            var alias = plugins[r]["extra_params"][param]["aliases"][0];
            params[alias]=new Array();
            for (option in plugins[r]["extra_params"][param]["options"]){
              params[alias].push(plugins[r]["extra_params"][param]["options"][option])
            }
            plugins_params[plugins[r]["name"]][alias] = (params[alias])
          }
        }
      }
    }
    document.getElementById('plugins').innerHTML = html;
    change_params();
  $(window).on('hashchange', hashchanged);
  hashchanged();
  $('.tooltip-form').tooltip();
});


function change_params(){
      var plugin = document.getElementById("plugins").options[document.getElementById("plugins").selectedIndex].value;

        html=""
        for (param in plugins_params[plugin]){
          if (param || plugins_params[plugin][param].length > 1){
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


