window.App = Ember.Application.create();
App.ApplicationAdapter = DS.FixtureAdapter;

jsPlumb.bind("ready", function () {
  jsPlumb.setRenderMode(jsPlumb.SVG);
  jsPlumb.Defaults.Anchor = ["TopCenter"];
  jsPlumb.Defaults.DragOptions = { cursor: 'wait', zIndex:20 };
  jsPlumb.Defaults.Connector = [ "Bezier", { curviness: 90 } ];
  jsPlumb.Defaults.Container = "pipeline-container";
});


App.Router.map(function () {
    this.resource('pipeline');
})

App.PipelineRoute = Em.Route.extend({
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

    setupController: function() {
        this.controllerFor('metaUnits').set('model', this.store.find('metaUnit'));
        this.controllerFor('pipeline').set('model', this.store.find('pipeline', 1));
        App.nodesController.set('model', this.store.find('unit'));
    }
});
