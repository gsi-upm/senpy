var ONYX = "http://www.gsi.dit.upm.es/ontologies/onyx/ns#";
var RDF_TYPE =  "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
var plugins_params = default_params = {};
var plugins = [];
var defaultPlugin = {};
var gplugins = {};
var pipeline = [];

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
    for(ix in response.plugins){
        plug = response.plugins[ix];
        plugins[plug.name] = plug;
    }
}

function get_datasets(response){
    datasets = response.datasets
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
    // Two elements with plugin class
    // One from the evaluate tab and another one from the analyse tab
    plugin_lists  = document.getElementsByClassName('plugin')
    for (element in plugin_lists){
        plugin_lists[element].innerHTML = html;
    }
    draw_plugin_pipeline();
}

function draw_plugin_pipeline(){
    var pipeHTML = "";
    console.log("Drawing pipeline: ", pipeline);
    for (ix in pipeline){
        plug = pipeline[ix];
        pipeHTML += '<span onclick="remove_plugin_pipeline(\'' + plug + '\')" class="btn btn-primary"><span ><i class="fa fa-minus"></i></span> ' + plug + '</span> <i class="fa fa-arrow-right"></i> ';
    }
    console.log(pipeHTML);
    $("#pipeline").html(pipeHTML);
}


function remove_plugin_pipeline(name){
    console.log("Removing plugin: ", name);
    var index = pipeline.indexOf(name);
    pipeline.splice(index, 1);
    draw_plugin_pipeline();

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

function add_plugin_pipeline(){
    var selected = get_selected_plugin();
    pipeline.push(selected);
    console.log("Adding ", selected);
    draw_plugin_pipeline();
}

function draw_datasets(){
    html = "";
    repeated_html = "<input class=\"checks-datasets\" type=\"checkbox\" value=\"";
    for (dataset in datasets){
        html += repeated_html+datasets[dataset]["@id"]+"\">"+datasets[dataset]["@id"];
        html += "<br>"
    }
    document.getElementById("datasets").innerHTML = html;
}

$(document).ready(function() {
    var response = JSON.parse($.ajax({type: "GET", url: "/api/plugins/" , async: false}).responseText);
    defaultPlugin= JSON.parse($.ajax({type: "GET", url: "/api/plugins/default" , async: false}).responseText);

    get_plugins(response);
    get_default_parameters();

    draw_plugins_list();
    draw_plugins_selection();
    draw_parameters();
    draw_plugin_description();

    if (evaluation_enabled) {
        var response2 = JSON.parse($.ajax({type: "GET", url: "/api/datasets/" , async: false}).responseText);
        get_datasets(response2);
        draw_datasets();
    }

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

function get_selected_plugin(){
    return document.getElementsByClassName('plugin')[0].options[document.getElementsByClassName('plugin')[0].selectedIndex].value;
}

function draw_default_parameters(){
    var basic_params = document.getElementById("basic_params");
    basic_params.innerHTML = params_div(default_params);
}

function update_params(params, plug){
    ep = plugins_params[plug];
    for(k in ep){
        params[k] = ep[k];
    }
    return params
}

function draw_extra_parameters(){
    var plugin = get_selected_plugin();
    get_parameters();

    var extra_params = document.getElementById("extra_params");
    var params = {};
    for (sel in pipeline){
        update_params(params, pipeline[sel]);
    }
    update_params(params, plugin);
    extra_params.innerHTML = params_div(params);
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

function get_pipeline_arg(){
    arg = "";
    for (ix in pipeline){
        arg = arg + pipeline[ix] + ",";
    }
    arg = arg + get_selected_plugin();
    return arg;
}


function load_JSON(){
    url = "/api";
    var container = document.getElementById('results');
    var rawcontainer = document.getElementById("jsonraw");
    rawcontainer.innerHTML = '';
    container.innerHTML = '';

    var plugin = get_pipeline_arg();
    $(".loading").addClass("loader");
    $("#preview").hide();

    var input = encodeURIComponent(document.getElementById("input").value);
    url += "?algo="+plugin+"&i="+input

    params = get_form_parameters();

    for (key in params){
        url += add_param(key, params[key]);
    }

    $.ajax({type: "GET", url: url}).always(function(response){
        document.getElementById("results-div").style.display = 'block';
        if(typeof response=="object") {
            var options = {
                mode: 'view'
            };
            var editor = new JSONEditor(container, options, response);
            editor.expandAll();
            $('#results-div a[href="#viewer"]').click();
            response = JSON.stringify(response, null, 4);
        } else {
            console.log("Got turtle?");
            $('#results-div a[href="#raw"]').click();
        }

        rawcontainer.innerHTML = replaceURLWithHTMLLinks(response);
        document.getElementById("input_request").innerHTML = "<a href='"+url+"'>"+url+"</a>"

        $(".loading").removeClass("loader");
        $("#preview").show();
    });
}

function get_datasets_from_checkbox(){
    var checks = document.getElementsByClassName("checks-datasets");

    datasets = "";
    for (var i = 0; i < checks.length; i++){
        if (checks[i].checked){
            datasets += checks[i].value + ",";
        }
    }
    datasets = datasets.slice(0, -1);
}


function create_body_metrics(evaluations){
	var new_tbody = document.createElement('tbody')
	var metric_html = ""
    for (var eval in evaluations){
        metric_html += "<tr><th>"+evaluations[eval].evaluates+"</th><th>"+evaluations[eval].evaluatesOn+"</th>";
        for (var metric in evaluations[eval].metrics){
            metric_html +=  "<th>"+parseFloat(evaluations[eval].metrics[metric].value.toFixed(4))+"</th>";
        }
        metric_html += "</tr>";
    }
    new_tbody.innerHTML = metric_html
    return new_tbody
}

function evaluate_JSON(){

    url = "/api/evaluate";

    var container = document.getElementById('results_eval');
    var rawcontainer = document.getElementById('jsonraw_eval');
    var table = document.getElementById("eval_table");

    rawcontainer.innerHTML = "";
    container.innerHTML = "";

    var plugin = document.getElementsByClassName("plugin")[0].options[document.getElementsByClassName("plugin")[0].selectedIndex].value;

    get_datasets_from_checkbox();

    url += "?algo="+plugin+"&dataset="+datasets

    $('#doevaluate').attr("disabled", true);
    $.ajax({type: "GET", url: url, dataType: 'json'}).always(function(resp) {
        $('#doevaluate').attr("disabled", false);
        response = resp.responseText;  

        rawcontainer.innerHTML = replaceURLWithHTMLLinks(response);

        document.getElementById("input_request_eval").innerHTML = "<a href='"+url+"'>"+url+"</a>"
        document.getElementById("evaluate-div").style.display = 'block';

        try {
            response = JSON.parse(response);
            var options = {
                mode: 'view'
            };

            //Control the single response results
            if (!(Array.isArray(response.evaluations))){
                response.evaluations = [response.evaluations]
            }

            new_tbody = create_body_metrics(response.evaluations)
            table.replaceChild(new_tbody, table.lastElementChild)

            var editor = new JSONEditor(container, options, response);
            editor.expandAll();
            // $('#results-div a[href="#viewer"]').tab('show');
            $('#evaluate-div a[href="#evaluate-table"]').click();
            // location.hash = 'raw';


        }
        catch(err){
            console.log("Error decoding JSON (got turtle?)");
            $('#evaluate-div a[href="#evaluate-raw"]').click();
            // location.hash = 'raw';
        }
    })
}

function draw_plugin_description(){
    var plugin = plugins[get_selected_plugin()];
    $("#plugdescription").text(plugin.description);
    console.log(plugin);
}

function plugin_selected(){
    draw_extra_parameters();
    draw_plugin_description();
}
