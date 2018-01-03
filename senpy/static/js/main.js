var ONYX = "http://www.gsi.dit.upm.es/ontologies/onyx/ns#";
var RDF_TYPE =  "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
var plugins_params = default_params = {};
var plugins = [];
var defaultPlugin = {};
var gplugins = {};

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


function get_plugins(response){
    plugins = response.plugins;
}

function group_plugins(){
    for (r in plugins){
        ptype = plugins[r]['@type'];
        if(gplugins[ptype] == undefined){
            gplugins[ptype] = [r];
        }else{
            gplugins[ptype].push(r);
	      }
    }
}

function get_parameters(){
    for (p in plugins){	
        plugin = plugins[p];
        if (plugin["extra_params"]){
            plugins_params[plugin["name"]] = plugin["extra_params"];
        }
    }
}

function draw_plugins_selection(){
    html="";
    group_plugins();
    for (g in gplugins){	
        html += "<optgroup label=\""+g+"\">"
        for (r in gplugins[g]){
            plugin = plugins[gplugins[g][r]]
            if (!plugin["name"]){
                console.log("No name for plugin ", plugin);
                continue;

            }
            html+= "<option value=\""+plugin.name+"\" "
            if (plugin["name"] == defaultPlugin["name"]){
                html+= " selected=\"selected\""
            }
            if (!plugin["is_activated"]){
                html+= " disabled=\"disabled\" "
            }
            html+=">"+plugin["name"]+"</option>"

        }
    }
    html += "</optgroup>"
    document.getElementById('plugins').innerHTML = html;
}

function draw_plugins_list(){
    var availablePlugins = document.getElementById('availablePlugins');

    for(p in plugins){
        var pluginEntry = document.createElement('li');
        plugin = plugins[p];
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
}

$(document).ready(function() {
    var response = JSON.parse($.ajax({type: "GET", url: "/api/plugins/" , async: false}).responseText);
    defaultPlugin= JSON.parse($.ajax({type: "GET", url: "/api/plugins/default" , async: false}).responseText);
    get_plugins(response);
    get_default_parameters();

    draw_plugins_list();
    draw_plugins_selection();
    draw_parameters();

    $(window).on('hashchange', hashchanged);
    hashchanged();
    $('.tooltip-form').tooltip();

});

function get_default_parameters(){
    default_params = JSON.parse($.ajax({type: "GET", url: "/api?help=true" , async: false}).responseText).valid_parameters;
    // Remove the parameters that are always added
    delete default_params["input"];
    delete default_params["algorithm"];
    delete default_params["help"];

}

function draw_default_parameters(){
    var basic_params = document.getElementById("basic_params");
    basic_params.innerHTML = params_div(default_params);
}

function draw_extra_parameters(){
    var plugin = document.getElementById("plugins").options[document.getElementById("plugins").selectedIndex].value;
    get_parameters();

    var extra_params = document.getElementById("extra_params");
    extra_params.innerHTML = params_div(plugins_params[plugin]);
}

function draw_parameters(){
    draw_default_parameters();
    draw_extra_parameters();
}


function add_default_params(){
    var html = "";
    // html += '<a href="#basic_params" class="btn btn-info" data-toggle="collapse">Basic API parameters</a>';
    html += '<span id="basic_params" class="panel-collapse collapse">';
    html += '<ul class="list-group">'
    html += params_div(default_params);
    html += '</span>';
    return html;
}

function params_div(params){
    var html = '<div class="container-fluid">';
    if (Object.keys(params).length === 0) {
        html += '<p class="text text-muted text-center">This plugin does not take any extra parameters</p>';
    }
    // Iterate over the keys in order
    pnames = Object.keys(params).sort()
    for (ix in pnames){
        pname = pnames[ix];
        param = params[pname];
        html+='<div class="form-group">';
        html += '<div class="row">'
        html+= '<label class="col-sm-4" for="'+pname+'">'+pname+'</label>'
        if (param.options){
            opts = param.options;
            if(param.options.length == 1 && param.options[0] == 'boolean') {
                opts = [true, false];
            }
            html+= '<select class="col-sm-8" id="'+pname+"\" name=\""+pname+"\">"
            var defaultopt = param.default;
            for (option in opts){
                isselected = "";
                if (defaultopt != undefined && opts[option] == defaultopt ){
                    isselected = ' selected="selected"'
                }
                html+="<option value=\""+opts[option]+'"' + isselected +
                '>'+opts[option]+"</option>"
            }
            html+="</select>"
        }
        else {
            default_value = "";
            if(param.default != undefined){
                default_value = param.default;
            };
            html +='<input class="col-sm-8" id="'+pname+'" name="'+pname+'" value="' + default_value + '"></input>';
        }
        html+='</div>';
        html+='<div class="row">';
        if ('description' in param){
            html += '<p class="form-text sm-sm-12 text-muted text-center">' + param.description + '</p>';

        }
        html+='</div>';
        html+='</div>';
    }
    html+='</div>';
    return html;
}

function _get_form_parameters(id){
    var element = document.getElementById(id);
    params = {};
    var selects = element.getElementsByTagName('select');
    var inputs = element.getElementsByTagName('input');

    Array.prototype.forEach.call(selects, function (sel) {
        key = sel.name;
        value = sel.options[sel.selectedIndex].value
        params[key] = value;
    });

    Array.prototype.forEach.call(inputs, function (el) {
        params[el.name] = el.value;
    });

    for (k in params){
        value = params[k];
        if (value == "" || value === "undefined"){
            delete params[k];

        }
    }

    return params;
}

function get_form_parameters(){
    var p1 = _get_form_parameters("basic_params");
    var p2 = _get_form_parameters("extra_params");
    return Object.assign(p1, p2);
}

function add_param(key, value){
    value = encodeURIComponent(value);
    return "&"+key+"="+value;
}

function load_JSON(){
    url = "/api";
    var container = document.getElementById('results');
    var rawcontainer = document.getElementById("jsonraw");
    rawcontainer.innerHTML = '';
    container.innerHTML = '';
    var plugin = document.getElementById("plugins").options[document.getElementById("plugins").selectedIndex].value;
    var input = encodeURIComponent(document.getElementById("input").value);
    url += "?algo="+plugin+"&i="+input

    params = get_form_parameters();

    for (key in params){
        url += add_param(key, params[key]);
    }

    var response =  $.ajax({type: "GET", url: url , async: false}).responseText;
    rawcontainer.innerHTML = replaceURLWithHTMLLinks(response);

    document.getElementById("input_request").innerHTML = "<a href='"+url+"'>"+url+"</a>"
    document.getElementById("results-div").style.display = 'block';
    try {
        response = JSON.parse(response);
        var options = {
            mode: 'view'
        };
        var editor = new JSONEditor(container, options, response);
        editor.expandAll();
        // $('#results-div a[href="#viewer"]').tab('show');
        $('#results-div a[href="#viewer"]').click();
        // location.hash = 'raw';
    }
    catch(err){
        console.log("Error decoding JSON (got turtle?)");
        $('#results-div a[href="#raw"]').click();
        // location.hash = 'raw';
    }
}
