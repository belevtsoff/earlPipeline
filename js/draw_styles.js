/* Define drawing styles for components, endpoints, etc.
 * 
 * Adapted from http://jsplumbtoolkit.com/demo/flowchart/jquery.html
 */

drawStyles = (function () {
    var mod = {};

    mod.connectorPaintStyle = {
        lineWidth:2,
        strokeStyle:"#216477",
        joinstyle:"round",
        outlineColor:"white",
        outlineWidth:2
    };

    // .. and this is the hover style. 
    mod.connectorHoverStyle = {
        lineWidth:2,
        strokeStyle:"#61B7CF",
        outlineWidth:2,
        outlineColor:"white"
    };

    mod.endpointHoverStyle = {
        fillStyle:"#61B7CF",
        strokeStyle:"#61B7CF"
    };
    
    // the definition of source endpoints (the small blue ones)
    mod.sourceEndpoint = {
        endpoint:"Dot",
        uniqueEndpoint: true,
        paintStyle:{ 
            strokeStyle:"#7AB02C",
            fillStyle:"white",
            radius:5,
            lineWidth:2 
        },				
        isSource:true,
        connectorStyle:mod.connectorPaintStyle,
        hoverPaintStyle:mod.endpointHoverStyle,
        connectorHoverStyle:mod.connectorHoverStyle,
        maxConnections:-1,
        dragOptions:{},
        anchor: [1, 0.5, 1, 0, 4, 0]
    };
    // the definition of target endpoints (will appear when the user drags a
    // connection) 
    mod.targetEndpoint = {
        endpoint:"Dot",					
        uniqueEndpoint: true,
        paintStyle:{ fillStyle:"#7AB02C",radius:6},
        hoverPaintStyle:mod.endpointHoverStyle,
        maxConnections:-1,
        dropOptions:{ hoverClass:"hover", activeClass:"active" },
        isTarget:true,			
        anchor: [0, 0.5, -1, 0, -4, 0]
    };

    return mod;
}());
