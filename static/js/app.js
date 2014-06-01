window.App = Ember.Application.create({
    currentPipeline: ''
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
            console.log(info);
        });
        jsPlumb.bind("connectionDetached", function (info) {
            pplController.send('disconnect', info);
            console.log(info);
        });
        jsPlumb.bind("connectionMoved", function (info) {
            pplController.send('move', info);
            console.log(info);
        });
    }
});

// some utility functions
// TODO: better place is to be found for this
App.util = {
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
            src + "_" + srcPort + "_endp",
            dst + "_" + dstPort + "_endp"
        ], editable:true, fireEvent: false});

        // link the underlying edge id to this connection
        connection.edge_id = edge.get('id');
    }
}
