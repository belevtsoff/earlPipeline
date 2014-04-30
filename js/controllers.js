App.MetaUnitsController = Ember.ArrayController.extend();

App.MetaUnitController = Ember.ObjectController.extend({
    actions: {
        addToPipeline: function() {
            var munit = this.get('model');

            // create unit from type
            var unit = this.store.createRecord('unit', {});
            unit.set('name', munit.get('name')+"-"+unit.get('id'));
            unit.set('type', munit);
            
            // add it to the pipeline
            this.store.find('pipeline', 1).then(function(pipeline) {
                pipeline.get('nodes').pushObject(unit);
            });
        }
    },
});

App.UnitController = Ember.ObjectController.extend();

App.nodesController = Ember.ArrayController.create();
