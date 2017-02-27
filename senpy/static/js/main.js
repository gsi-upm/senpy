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
    var availablePlugins = document.getElementById('availablePlugins');
    plugins = response.plugins;
    for (r in plugins){
      plugin = plugins[r]
      if (plugin["name"]){
        if (plugin["name"] == defaultPlugin["name"]){
          if (plugin["is_activated"]){
            html+= "<option value=\""+plugin["name"]+"\" selected=\"selected\">"+plugin["name"]+"</option>"
          }else{
            html+= "<option value=\""+plugin["name"]+"\" selected=\"selected\" disabled=\"disabled\">"+plugin["name"]+"</option>"
          }
        }
        else{
          if (plugin["is_activated"]){
            html+= "<option value=\""+plugin["name"]+"\">"+plugin["name"]+"</option>"
          }
          else{
            html+= "<option value=\""+plugin["name"]+"\" disabled=\"disabled\">"+plugin["name"]+"</option>"
          }
        }
      }
      if (plugin["extra_params"]){
        plugins_params[plugin["name"]]={};
        for (param in plugin["extra_params"]){
          if (typeof plugin["extra_params"][param] !="string"){
            var params = new Array();
            var alias = plugin["extra_params"][param]["aliases"][0];
            params[alias]=new Array();
            for (option in plugin["extra_params"][param]["options"]){
              params[alias].push(plugin["extra_params"][param]["options"][option])
            }
            plugins_params[plugin["name"]][alias] = (params[alias])
          }
        }
      }
      var pluginList = document.createElement('li');
      
      newHtml = ""
      if(plugin.url) {
        newHtml= "<a href="+plugin.url+">" + plugin.name + "</a>";
      }else {
        newHtml= plugin["name"];
      }
      newHtml += ": " + replaceURLWithHTMLLinks(plugin.description);
      pluginList.innerHTML = newHtml;
      availablePlugins.appendChild(pluginList)
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
      var container = document.getElementById('results');
      var rawcontainer = document.getElementById("jsonraw");
      rawcontainer.innerHTML = '';
      container.innerHTML = '';
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
      var options = {
        mode: 'view'
      };
      var editor = new JSONEditor(container, options, response);
      editor.expandAll();
      rawcontainer.innerHTML = replaceURLWithHTMLLinks(JSON.stringify(response, undefined, 2))
      document.getElementById("input_request").innerHTML = "<a href='"+url+"'>"+url+"</a>"
      document.getElementById("results-div").style.display = 'block';
      

}


