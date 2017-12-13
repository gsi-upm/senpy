var ONYX = "http://www.gsi.dit.upm.es/ontologies/onyx/ns#";
var RDF_TYPE =  "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
var plugins_params={};
var default_params = JSON.parse($.ajax({type: "GET", url: "/api?help=true" , async: false}).responseText);
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
    gplugins = {};
    for (r in plugins){
        ptype = plugins[r]['@type'];
        if(gplugins[ptype] == undefined){
            gplugins[ptype] = [r]
        }else{
            gplugins[ptype].push(r)
	      }
	  }
    for (g in gplugins){	
        html += "<optgroup label=\""+g+"\">"
        for (r in gplugins[g]){
            plugin = plugins[gplugins[g][r]]
            if (!plugin["name"]){
                console.log("No name for plugin ", plugin);
                continue;

            }
            html+= "<option value=\""+plugin["name"]+"\" "
            if (plugin["name"] == defaultPlugin["name"]){
                html+= " selected=\"selected\""
            }
            if (!plugin["is_activated"]){
                html+= " disabled=\"disabled\" "
            }
            html+=">"+plugin["name"]+"</option>"
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
        var pluginEntry = document.createElement('li');
        
        newHtml = ""
        if(plugin.url) {
            newHtml= "<a href="+plugin.url+">" + plugin.name + "</a>";
        }else {
            newHtml= plugin["name"];
        }
        newHtml += ": " + replaceURLWithHTMLLinks(plugin.description);
        pluginEntry.innerHTML = newHtml;
        availablePlugins.appendChild(pluginEntry)
    }
    html += "</optgroup>"
    document.getElementById('plugins').innerHTML = html;
    change_params();
    
    $(window).on('hashchange', hashchanged);
    hashchanged();
    $('.tooltip-form').tooltip();

});


function change_params(){
      var plugin = document.getElementById("plugins").options[document.getElementById("plugins").selectedIndex].value;
        html=""
		for (param in default_params){
		  if ((default_params[param]['options']) && (['help','conversion'].indexOf(param) < 0)){  
          html+= "<label> "+param+"</label>"
          if (default_params[param]['options'].length < 1) {
              html +="<input></input>";
          }
          else {
              html+= "<select id=\""+param+"\" name=\""+param+"\">"
              for (option in default_params[param]['options']){
                  if (default_params[param]['options'][option] == default_params[param]['default']){  
                      html+="<option value \""+default_params[param]['options'][option]+"\" selected >"+default_params[param]['options'][option]+"</option>"
                  }
                  else{
                      html+="<option value \""+default_params[param]['options'][option]+"\">"+default_params[param]['options'][option]+"</option>"
                      
                  }
              }
          }
      html+="</select><br>"
      }
		}
        for (param in plugins_params[plugin]){
          if (param || plugins_params[plugin][param].length > 1){
              html+= "<label> Parameter "+param+"</label>"
              param_opts = plugins_params[plugin][param]
              if (param_opts.length > 0) {
                  html+= "<select id=\""+param+"\" name=\""+param+"\">"
                  for (option in param_opts){
                      html+="<option value \""+param_opts[option]+"\">"+param_opts[option]+"</option>"
                  }
                  html+="</select>"
              }
              else {
                  html +="<input id=\""+param+"\" name=\""+param+"\"></input>";
              }
          }
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
            field = document.getElementById(param);
            if (plugins_params[plugin][param].length > 0){
                var param_value = encodeURIComponent(field.options[field.selectedIndex].text);
            } else {
                var param_value = encodeURIComponent(field.text);
            }
            if (param_value !== "undefined" && param_value.length > 0){
                url+="&"+param+"="+param_value
            }
        }
      }

      for (param in default_params){
        if ((param != null) && (default_params[param]['options']) && (['help','conversion'].indexOf(param) < 0)){
            var param_value = encodeURIComponent(document.getElementById(param).options[document.getElementById(param).selectedIndex].value);
            if (param_value){
              url+="&"+param+"="+param_value
            }
        }
      }

  var response =  $.ajax({type: "GET", url: url , async: false}).responseText;
  rawcontainer.innerHTML = replaceURLWithHTMLLinks(response)

  document.getElementById("input_request").innerHTML = "<a href='"+url+"'>"+url+"</a>"
  document.getElementById("results-div").style.display = 'block';
  try {
    response = JSON.parse(response);
      var options = {
        mode: 'view'
      };
      var editor = new JSONEditor(container, options, response);
      editor.expandAll();
  }
  catch(err){
    console.log("Error decoding JSON (got turtle?)");
  }
      

}


