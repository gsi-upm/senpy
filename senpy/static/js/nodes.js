ns = {
    'http://www.gsi.upm.es/ontologies/marl/ns#': 'marl',
    'http://www.gsi.upm.es/ontologies/onyx/ns#': 'onyx',
    'http://www.gsi.upm.es/ontologies/senpy/ns#': 'onyx',
    'http://www.gsi.upm.es/onto/senpy/ns#': 'senpy',
    'http://www.w3.org/ns/prov#': 'prov',
    'http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#': 'nif'
}

mappings = {
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type': 'a',
}

function load_graph(){

    function filterNodesById(nodes,id){
        return nodes.filter(function(n) { return n.id === id; });
    }

    function filterNodesByType(nodes,value){
        return nodes.filter(function(n) { return n.type === value; });
    }

    function triplesToGraph(triples){

        svg.html("");
        //Graph
        var graph={nodes:[], links:[], triples: []};

        triples = triples.filter(t=>t!=null).map(t => {
            return t.map(e =>{
                ids = e.match(/^\<(.*)\>/)
                if (! ids ) {
                    return e
                    
                }
                id = ids[1]
                for (ix in ns) {
                    id = id.replace(ix, ns[ix] + ':')
                }
                if (! (id in mappings)) {
                    console.log(id, id in mappings)
                    return id
                }
                return mappings[id]
            })
        })

        //Initial Graph from triples
        triples.forEach(function(triple){
            if (triple == null) {
                return
            }
            var subjId = triple[0];
            var predId = triple[1];
            var objId = triple[2];



            var subjNode = filterNodesById(graph.nodes, subjId)[0];
            var objNode  = filterNodesById(graph.nodes, objId)[0];

            if(subjNode==null){
                subjNode = {id:subjId, label:subjId, weight:1, type:"node"};
                graph.nodes.push(subjNode);
            }

            if(objNode==null){
                objNode = {id:objId, label:objId, weight:1, type:"node"};
                graph.nodes.push(objNode);
            }

            var predNode = {id:predId, label:predId, weight:1, type:"pred"} ;
            graph.nodes.push(predNode);

            var blankLabel = "";

            graph.links.push({source:subjNode, target:predNode, predicate:blankLabel, weight:1});
				    graph.links.push({source:predNode, target:objNode, predicate:blankLabel, weight:1});
            graph.triples.push({s:subjNode, p:predNode, o:objNode});


        });

        return graph;
    }


    function update(graph){


        // ==================== Add Marker ====================
        svg.append("svg:defs").selectAll("marker")
            .data(["end"])
            .enter().append("svg:marker")
            .attr("id", String)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 30)
            .attr("refY", -0.5)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("svg:polyline")
            .attr("points", "0,-5 10,0 0,5")
        ;


        // ==================== Add Links ====================
			  var links = svg.selectAll(".link")
						.data(graph.triples)
						.enter()
						.append("path")
						.attr("marker-end", "url(#end)")
						.attr("class", "link")
				;
				;//links

        // ==================== Add Link Names =====================
			  var linkTexts = svg.selectAll(".link-text")
		        .data(graph.triples)
		        .enter()
		        .append("text")
						.attr("class", "link-text")
						.text( function (d) { return d.p.label; })
				;


        //linkTexts.append("title")
        //		.text(function(d) { return d.predicate; });

        // ==================== Add Link Names =====================
        var nodeTexts = svg.selectAll(".node-text")
            .data(filterNodesByType(graph.nodes, "node"))
            .enter()
            .append("text")
            .attr("class", "node-text")
            .text( function (d) { return d.label; })
        ;
        //nodeTexts.append("title")
        //		.text(function(d) { return d.label; });

        // ==================== Add Node =====================
        var nodes = svg.selectAll(".node")
            .data(filterNodesByType(graph.nodes, "node"))
            .enter()
            .append("circle")
            .attr("class", "node")
            .attr("r",8)
            .call(force.drag)
        ;//nodes

        // ==================== Add Predicate =====================
        /*var preds = svg.selectAll(".node")
          .data(graph.preds)
          .enter()
          .append("circle")
          .attr("class", "node")
          .attr("r",1)
          //.call(force.drag)*/
        ;//nodes

        // ==================== Force ====================
        force.on("tick", function() {
				    nodes
					      .attr("cx", function(d){ return d.x; })
					      .attr("cy", function(d){ return d.y; })
					  ;

            links
                .attr("d", function(d) {
                    return "M" 	+ d.s.x + "," + d.s.y
                        + "S" + d.p.x + "," + d.p.y
                        + " " + d.o.x + "," + d.o.y;
                })
            ;

            nodeTexts
                .attr("x", function(d) { return d.x + 12 ; })
                .attr("y", function(d) { return d.y + 3; })
            ;


				    linkTexts
					      .attr("x", function(d) { return 4 + (d.s.x + d.p.x + d.o.x)/3  ; })
					      .attr("y", function(d) { return 4 + (d.s.y + d.p.y + d.o.y)/3 ; })
					  ;        });

        // ==================== Run ====================
        force
            .nodes(graph.nodes)
            .links(graph.links)
            .charge(-500)
            .linkDistance(50)
            .start()
        ;
    }

    get_result('ntriples').done(resp => {
        triples = resp.split('\n').map(line => line.match(/[^" ][^ ]*|\"[^"]+\"[^ ]*/g))

        console.log(triples);


        var graph = triplesToGraph(triples);
        console.log(graph);

        update(graph);
    }).fail(resp => {
        alert('Could not get a response.');
    });

    d3.select('#svg-body').selectAll("*").remove();
    var svg = d3.select("#svg-body").append("svg")
		    .attr("width", width)
		    .attr("height", height)
    ;

    var height = 600;
    var width = $('.tab-content').width();

    console.log('Graph with', width, height);
    var force = d3.layout.force().size([width, height]);
}
