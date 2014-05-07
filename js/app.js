window.App = Ember.Application.create();
App.ApplicationAdapter = DS.FixtureAdapter;

jsPlumb.bind("ready", function () {
  jsPlumb.setRenderMode(jsPlumb.SVG);
  jsPlumb.Defaults.Anchor = ["TopCenter"];
  jsPlumb.Defaults.DragOptions = { cursor: 'wait', zIndex:20 };
  jsPlumb.Defaults.Connector = [ "Bezier", { curviness: 90 } ];
  jsPlumb.Defaults.Container = "pipeline-container";
});

// routes
App.Router.map(function () {
    this.resource('pipelines');
    this.resource('pipeline', {path: "/pipeline/:pipeline_id"});
})

App.PipelineRoute = Em.Route.extend({
    model: function(params) {
        this.store.find('metaUnit'); //init fixtures
        this.store.find('unit'); //init fixtures
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
        this.controllerFor('pipeline').set('model', pplModel);
        this.controllerFor('metaUnits').set('model', this.store.find('metaUnit'));

        // bind connection events to the proper handler
        jsPlumb.unbind("connection");
        jsPlumb.bind("connection", function (info) {
            pplController.send('jsPlumbConnect', info);
        })
    }
});

