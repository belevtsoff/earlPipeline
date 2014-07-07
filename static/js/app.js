window.App = Ember.Application.create({
    currentPipeline: '',
    namespace: 'api',
});
//App.ApplicationAdapter = DS.FixtureAdapter;

jsPlumb.bind("ready", function () {
  jsPlumb.setRenderMode(jsPlumb.SVG);
  jsPlumb.Defaults.Anchor = ["TopCenter"];
  jsPlumb.Defaults.DragOptions = { cursor: 'wait', zIndex:20 };
  jsPlumb.Defaults.Connector = [ "Bezier", { curviness: 90 } ];
  jsPlumb.Defaults.Container = "pipeline-container";
});

// routes
App.Router.map(function () {
    this.resource('pipelines', {path: "/pipelines"}, function() {
        this.route('new', {path: "/new"});
    });
    this.resource('pipeline', {path: "/pipelines/:pipeline_id"});
});

App.IndexRoute = Ember.Route.extend({
    beforeModel: function() {
        this.transitionTo('pipelines');
    }
});

App.PipelinesRoute = Ember.Route.extend({
    model: function() {
        return this.store.find('pipeline');
    },

    setupController: function(controller, model) {
        controller.set('model', model);

        // initialize a WebSocket connection for event passing. This connection is mainly for status event passing
        var url = App.util.create_pipelines_url('event_bus');
        
        var conn_id = Date.now();
        url = App.util.create_ws_origin() + url + "?connId=" + conn_id;

        var ws = new WebSocket(url);
        App.util.bind_websocket(ws, controller);
    },

    actions: {
        // cleanup
        willTransition: function(transition) {
            this.get('controller.event_bus').close();
        }
    }
})

App.PipelineRoute = Em.Route.extend({
    model: function(params) {
        return this.store.find('pipeline', params.pipeline_id);
    },

    renderTemplate: function () {

        this.render('pipeline');

        this.render('pipeline-units', {
            into: 'pipeline',
            outlet: 'pipeline-units',
            controller: this.controllerFor('pipeline')
        });

        this.render('pipeline-controls', {
            into: 'pipeline',
            outlet: 'pipeline-controls',
            controller: this.controllerFor('pipeline')
        });

        this.render('meta-units', {
            into: 'pipeline',
            outlet: 'meta-units',
            controller: this.controllerFor('metaUnits')
        });
    },

    activate: function() {
        var pplModel = this.modelFor('pipeline');
        var pplController = this.controllerFor('pipeline');
        
        // Update the 'currentPipeline' property. This is needed to form proper
        // server API calls when working with units/edges. Fired whenever the
        // route is changed
        App.set('currentPipeline', pplModel);
        
        // bind connection events to the proper handler
        jsPlumb.bind("connection", function (info) {
            pplController.send('connect', info);
        });
        jsPlumb.bind("connectionDetached", function (info) {
            pplController.send('disconnect', info);
        });
        jsPlumb.bind("connectionMoved", function (info) {
            pplController.send('move', info);
        });

        // initialize a WebSocket connection for event passing
        var url = App.util.create_pipeline_url(pplModel.get('id'), 'event_bus');
        var conn_id = Date.now();
        url = App.util.create_ws_origin() + url + "?connId=" + conn_id;

        var ws = new WebSocket(url);
        App.util.bind_websocket(ws, pplController);
    },

    setupController: function(pplController, pplModel) {
        // set up controllers with proper models
        this.controllerFor('pipeline').set('model', pplModel);
        this.controllerFor('metaUnits').set('model', this.store.find('metaUnit'));
        //this.controllerFor('pipelines').set('model', this.store.find('pipeline'));

    },

    actions: {
        // cleanup
        willTransition: function(transition) {
            jsPlumb.unbind("connection");
            jsPlumb.unbind("connectionDetached");
            jsPlumb.unbind("connectionMoved");

            this.controllerFor('pipeline').edgesLoaded = false;
            
            // When loading a new pipeline, unload all the units and edges
            // from the cache to avoid naming conflicts
            this.store.unloadAll('edge');
            this.store.unloadAll('unit');

            this.get('controller.event_bus').close();
        }
    }
});

// some utility functions
// TODO: better place is to be found for this
App.util = {
    // many underscores to avoid conflicts
    id_template: "uname___%@___pname___%@___%@",
    id_regexp: "uname___(.*)___pname___(.*)___(?:prt|endp)",

    // Status stuff
    status_codes: {
        FINISHED: 1,
        RUNNING: 2,
        FAILED: 3,
    },

    /* Given an 'edge' data object, looks up the corresponding graphical
    * elements and creates a graphical link between the respective ports of the
    * corresponding units. This function should be used to add a graphical
    * connection between elements, when the corresponding edge object is
    * already present in the database */
    plumbConnect: function (edge) {
        var src = edge.get('src.id');
        var srcPort = edge.get('srcPort');
        var dst = edge.get('dst.id');
        var dstPort = edge.get('dstPort');

        var connection = jsPlumb.connect({uuids:[
            this.create_endpoint_id(src, srcPort),
            this.create_endpoint_id(dst, dstPort)
        ], editable:true, fireEvent: false});

        // link the underlying edge id to this connection
        connection.edge_id = edge.get('id');
    },

    /* Used to create a unique port identifier string, which consists of an if
     * of a containing unit, and the name of the port itself. Such identifiers
     * are then used by jsPlumb to avoid naming conflicts, because it doesn't
     * know about the existence of units, only about ports, and their names are
     * only guaranteed to be unique within a unit. Therefore, a unit name is
     * required to construct a unique port id.
     *
     * Neither unit nor port names should contain columns or other special
     * characters, except minus or underscore
     *
     * @param {string} unit_name Name of the containing unit
     * @param {string} port_name Name of the port
     *
     * @returns {string} A unique port identifier */
    create_port_id: function (unit_name, port_name) {
        return Em.String.fmt(this.id_template, [unit_name, port_name, "prt"])
    },

    /* Create unique endpoint identifier. Same as 'create_port_id', but with
     * appended ending
     *
     * @param {string} unit_name Name of the containing unit
     * @param {string} port_name Name of the port
     *
     * @returns {string} A unique endpoint identifier
     * */
    create_endpoint_id: function (unit_name, port_name) {
        return Em.String.fmt(this.id_template, [unit_name, port_name, "endp"])
    },

    /* Splits a unique port or endpoint id into unit_name and port_name. The
     * main assumption is that neither unit nor port names contain columns.
     *
     * @param {string} uid A port or endpoint id to split
     *
     * @returns {Object} an object containing two string fields: 'unit_name'
     * and 'port_name'
     */
    split_port_endp_id: function (uid) {
        var re = RegExp(this.id_regexp);
        var m = re.exec(uid);

        if (m) {
            return {
                unit_name: m[1],
                port_name: m[2]
            }
        }

        else {
            throw "Wrong port identifier! Make sure your backend doesn't have special symbols in the port names";
        }
    },

    /* Given log msg object, constructs a decorated html string to be inserted in the page
     *
     * @param {Object} msg Object to convert
     */
    log_event_to_html: function(data) {
        // TODO: add some actual decoration
        var res = data.msg;
        if(data.src.pipeline) {
            if(data.src.unit) {
                res = data.src.pipeline+"."+data.src.unit+": "+res;
            }
            else {
                res = data.src.pipeline+": "+res;
            }
        }
        else {
            res = "server: "+res;
        }

        return res;
    },

    /* Creates a url to the specified pipeline, based on the current adapter
     * settings
     *
     * @param {string} pipeline_id Id of the pipeline
     * @param {string} endpoint Endpoint for the current url
     */
    create_pipeline_url: function(pipeline_id, endpoint) {
        // TODO: this is still ugly
        var url = App.__container__.lookup('adapter:application')
            .buildURL('pipeline', pipeline_id)
        return url + '/' + endpoint
    },

    /* Creates a url to pipelines, based on the current adapter
     * settings
     *
     * @param {string} endpoint Endpoint for the current url
     */
    create_pipelines_url: function(endpoint) {
        // TODO: this is still ugly
        var url = App.__container__.lookup('adapter:application')
            .buildURL('pipelines')
        return url + '/' + endpoint
    },

    /* Constructs origin for a WebSocket URL */
    create_ws_origin: function() {
        return window.location.origin.replace('http', 'ws');
    },

    bind_websocket: function(ws, controller) {
        ws.onopen = function() {
            controller.set("event_bus", ws);
        };
        ws.onmessage = function (evt) {
            controller.send("handle_server_event", evt.data);
        };
        ws.onclose = function(evt) {
            if(!evt.wasClean)
                alert('Event-stream connection to server is dropped for some reason! Try reloading the page.');
        }
    }
}
