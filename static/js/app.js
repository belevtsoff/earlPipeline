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
    this.resource('pipeline', {path: "/pipelines/:pipeline_id"});
});

App.PipelineRoute = Em.Route.extend({
    model: function(params) {
        // When loading a new pipeline, unload all the units and edges from the
        // cache to avoid naming conflicts
        this.store.unloadAll('unit');
        this.store.unloadAll('edge');
        return this.store.find('pipeline', params.pipeline_id)
    },

    renderTemplate: function () {

        this.render('pipeline', {
            into: 'application',
            outlet: 'pipeline',
            controller: this.controllerFor('pipeline')
        });

        this.render('pipelineControls', {
            into: 'application',
            outlet: 'pipelineControls',
            controller: this.controllerFor('pipeline')
        });

        this.render('metaUnits', {
            into: 'application',
            outlet: 'units',
            controller: this.controllerFor('metaUnits')
        });
    },

    setupController: function(pplController, pplModel) {
        // Update the 'currentPipeline' property. This is needed to form proper
        // server API calls when working with units/edges. Fired whenever the
        // route is changed
        App.set('currentPipeline', pplModel);

        // set up controllers with proper models
        this.controllerFor('pipeline').set('model', pplModel);
        this.controllerFor('metaUnits').set('model', this.store.find('metaUnit'));
        //this.controllerFor('pipelines').set('model', this.store.find('pipeline'));

        // bind connection events to the proper handler
        jsPlumb.unbind("connection");
        jsPlumb.unbind("connectionDetached");
        jsPlumb.unbind("connectionMoved");
        jsPlumb.bind("connection", function (info) {
            pplController.send('connect', info);
        });
        jsPlumb.bind("connectionDetached", function (info) {
            pplController.send('disconnect', info);
        });
        jsPlumb.bind("connectionMoved", function (info) {
            pplController.send('move', info);
        });
    }
});

// some utility functions
// TODO: better place is to be found for this
App.util = {
    // many underscores to avoid conflicts
    id_template: "uname___%@___pname___%@___%@",
    id_regexp: "uname___(.*)___pname___(.*)___(?:prt|endp)",

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
    }

}
