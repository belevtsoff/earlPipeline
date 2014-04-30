App.MetaUnitsController = Ember.ArrayController.extend();

App.MetaUnitController = Ember.ObjectController.extend({
    needs: ['pipeline'], // where to add units
    actions: {
        addToPipeline: function() {
            var munit = this.get('model');

            // create unit from type
            var unit = this.store.createRecord('unit', {});
            unit.set('name', munit.get('name')+"-"+unit.get('id'));
            unit.set('type', munit);
            
            // add it to the pipeline
            this.get('controllers.pipeline.nodes').pushObject(unit);
        }
    },
});

App.UnitController = Ember.ObjectController.extend({
    actions:{
        savePosition: function (position) {
            this.set('model.top', position.top);
            this.set('model.left', position.left);
            this.get('model').save();
        }
    }
});
