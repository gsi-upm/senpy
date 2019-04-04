var ONYX = "http://www.gsi.dit.upm.es/ontologies/onyx/ns#";
var RDF_TYPE =  "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
var plugins_params = default_params = {};
var plugins = [];
var defaultPlugin = {};
var gplugins = {};
var pipeline = [];
var converter = new showdown.Converter({simplifiedAutoLink: true});

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
    console.log('Hash changed');
    var hash = location.hash,
        hashPieces = hash.split('?');
    loc = hashPieces[0]
    if( loc.length > 0 ){

        if(loc[loc.length-1] == '.' ){
            loc = loc.slice(0, -1)
        }
        console.log(loc)
        activeTab = $('[href=' + loc + ']');
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

function draw_plugins_selection(){
    html="";
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
        html += "</optgroup>"
    }
    // Two elements with plugin class
    // One from the evaluate tab and another one from the analyse tab
    $('#plugins-select').html(html)
    draw_plugin_pipeline();
}

function draw_plugins_eval_selection(){
    evaluable = JSON.parse($.ajax({type: "GET", url: "/api/plugins/?plugin_type=Evaluable" , async: false}).responseText).plugins;

    html="";
    for (r in evaluable){
        plugin = evaluable[r]
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

    // Two elements with plugin class
    // One from the evaluate tab and another one from the analyse tab
    $('#plugins-eval').html(html)
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

    availablePlugins.innerHTML = '';
    html = ''

    for (g in gplugins){	
        for (r in gplugins[g]){
            p = gplugins[g][r];
            plugin = plugins[p];
            html += `<div class="card my-2">
    <div class="card-body">
    <h4 class="card-title"> ${plugin.name} <span class="badge badge-success">${plugin.version}</span>`
            // if (typeof plugin.author !== 'undefined'){
            //     html += ` <span class="badge badge-secondary">${plugin.author}</span>`
            // }
            // for (ptype in plugin['@type'] ){
                html += ` <span class="badge badge-secondary">${plugin['@type']}</span>`
            // }
            html += `</h4>
    <p class="card-text">${converter.makeHtml(plugin.description)}</p>
    </div>
</div>`
            html += "</div>";
        }
    }
    availablePlugins.innerHTML = html;
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
    var response = JSON.parse($.ajax({type: "GET", url: "/api/plugins/?verbose=1" , async: false}).responseText);
    defaultPlugin= JSON.parse($.ajax({type: "GET", url: "/api/plugins/default" , async: false}).responseText);

    get_plugins(response);
    get_default_parameters();

    group_plugins();
    draw_plugins_selection();
    draw_plugins_eval_selection();
    draw_parameters();
    draw_plugins_list();
    draw_plugin_description();
    example_selected();

    if (evaluation_enabled) {
        var response2 = JSON.parse($.ajax({type: "GET", url: "/api/datasets/" , async: false}).responseText);
        get_datasets(response2);
        draw_datasets();
    }

    $(window).on('hashchange', hashchanged);
    hashchanged();
    $('.tooltip-form').tooltip();

    $('.nav-pills a').on('shown.bs.tab', function (e) {
        window.location.hash = e.target.hash + '.';
    })
    $('form').on("submit",function( event ) {
        event.preventDefault();
    });

});

function get_parameters(plugin, verbose){
    verbose = typeof verbose !== 'undefined' ? verbose : false;
    resp = JSON.parse($.ajax({type: "GET", url: "/api/"+plugin+"?help=true&verbose=" + verbose , async: false}).responseText)
    params = resp.valid_parameters;
    // Remove the parameters that are always added
    delete params["input"];
    delete params["algorithm"];
    delete params["outformat"];
    delete params["help"];
    return params
}

function get_default_parameters() {
    default_params = get_parameters('default', true);
}

function get_selected_plugin(){
    return document.getElementsByClassName('plugin')[0].options[document.getElementsByClassName('plugin')[0].selectedIndex].value;
}

function draw_default_parameters(){
    bp = $('#basic_params');
    console.log(bp)
     bp.html(params_div(default_params));
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
    if (typeof plugins_params[plugin] === 'undefined' ){
        params = get_parameters(plugin, false);
        plugins_params[plugin] = params;
    }

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
    var html = "<form>";
    // html += '<a href="#basic_params" class="btn btn-info" data-toggle="collapse">Basic API parameters</a>';
    html += params_div(default_params);
    html += '</form>'
    return html;
}

function params_div(params){
    var html = '';
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

            html += '<small class="form-text sm-sm-12 text-muted">' 
            html += converter.makeHtml(param.description) + '</small>';

        }
        html+='</div>';
        html+='</div>';
    }
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


function get_result(outformat, cb, eb) {
    url = "/api";
    $('.results').html('');

    var plugin = get_pipeline_arg();
    $(".loading").addClass("loader");
    $("#preview").hide();


    var input = encodeURIComponent(document.getElementById("input").value);

    url += "?algo="+plugin+"&i="+input+"&outformat="+outformat;

    params = get_form_parameters();

    for (key in params){
        url += add_param(key, params[key]);
    }

    return $.ajax({type: "GET", url: url}).done(function(){
        $(".loading").removeClass("loader");
        $("#preview").show();
    })
}

function load_results(outformat){

    if (typeof outformat === 'undefined') {
        active = $('#results-container .tab-pane.active').get(0);
        console.log(active.id);
        outformat = active.id
        if (outformat == 'viewer') {
            outformat = 'json-ld';
        }
    }

    get_result(outformat).always(function(response, txt, request){
        console.log('outformat is', outformat)
        document.getElementById("results-div").style.display = 'block';
        container = $('#results-'+outformat).get(0);
        raw = '';

        try {
            raw = replaceURLWithHTMLLinks(response)
        }catch(error){
            response = JSON.stringify(response, null, 1);
            raw = syntaxHighlight(response)
        }
        console.log('highlighted');
        container.innerHTML = replaceURLWithHTMLLinks(raw);

        document.getElementById("input_request").innerHTML = "<a href='"+url+"'>"+url+"</a>"
        console.log("Request failed", request);
        $(".loading").removeClass("loader");
        $("#preview").show();
    }).fail(function(data) {
        if (data.readyState == 0) {
            $('#results-'+outformat).html('');
            alert( "The server is not responding. Make sure it is still running." );
        }
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
        metric_html += "<tr><td>"+evaluations[eval].evaluates+"</td><td>"+evaluations[eval].evaluatesOn+"</td>";
        for (var metric in evaluations[eval].metrics){
            var value = "Not available";
            try {
                value = parseFloat(evaluations[eval].metrics[metric].value.toFixed(4));
            }catch(err){
            }
            metric_html +=  "<td>"+value+"</td>";
        }
        metric_html += "</tr>";
    }
    new_tbody.innerHTML = metric_html
    return new_tbody
}

function evaluate_JSON(){
    $(".loading").addClass("loader");

    url = "/api/evaluate";

    var container = document.getElementById('results_eval');
    var rawcontainer = document.getElementById('jsonraw_eval');
    var table = document.getElementById("eval_table");

    rawcontainer.innerHTML = "";
    container.innerHTML = "";
    $("#evaluate-div").hide();

    var plugin = $("#plugins-eval option:selected").val();

    get_datasets_from_checkbox();

    url += "?algo="+plugin+"&dataset="+datasets

    $('#doevaluate').attr("disabled", true);
    $.ajax({type: "GET", url: url, dataType: 'text'}).always(function(response) {
        $('#doevaluate').attr("disabled", false);

        document.getElementById("input_request_eval").innerHTML = "<a href='"+url+"'>"+url+"</a>"
        document.getElementById("evaluate-div").style.display = 'block';

        $('#evaluate-div a[href="#evaluate-raw"]').click();

        try {
            js = JSON.parse(response);
            rawcontainer.innerHTML = replaceURLWithHTMLLinks(response);
        }
        catch(err){
            console.log("Error decoding JSON");
            if (typeof(response.responseText) !== 'undefined') {
                rawcontainer.innerHTML = response.responseText;
            }
            else {
                rawcontainer.innerHTML = response;
            }
            $(".loading").removeClass("loader");
            $('#evaluate-div a[href="#evaluate-raw"]').click();
            return
        }

        if (typeof(js['senpy:evaluations']) === 'undefined') {
            alert('Could not evaluate on that dataset');
        } else {
            //Control the single response results
            if (!(Array.isArray(js['senpy:evaluations']))){
                js['senpy:evaluations'] = [js['senpy:evaluations']]
                rawcontainer.innerHtml = response;
            }
            new_tbody = create_body_metrics(js['senpy:evaluations'])
            table.replaceChild(new_tbody, table.lastElementChild)
            $('#evaluate-div a[href="#evaluate-table"]').click();
            // location.hash = 'raw';
            $("#evaluate-div").show();
        }

        $(".loading").removeClass("loader");


    })
}

function draw_plugin_description(){
    var plugin = plugins[get_selected_plugin()];
    $("#plugdescription").html(converter.makeHtml(plugin.description));
    console.log(plugin);
}

function plugin_selected(){
    draw_extra_parameters();
    draw_plugin_description();
}

function example_selected(){
    console.log('changing text');
    var text = $('#examples option:selected').data("text");
    $('#input').val(text);
    console.log('done');
}

function syntaxHighlight(json) {
    if (typeof json != 'string') {
        json = JSON.stringify(json, undefined, 1);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
    if (/:$/.test(match)) {
        cls = 'key';
    } else {
        cls = 'string';
    }
} else if (/true|false/.test(match)) {
    cls = 'boolean';
} else if (/null/.test(match)) {
    cls = 'null';
}
return '<span class="' + cls + '">' + match + '</span>';
});
}
