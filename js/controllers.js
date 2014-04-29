App.MetaUnitsController = Ember.ArrayController.extend();

App.MetaUnitController = Ember.ObjectController.extend({
    actions: {
        addToPipeline: function() {
            var munit = this.get('model');
            var unit = this.store.createRecord('unit', this.newUnit(munit));
            unit.set('name', munit.get('typeName')+"-"+unit.get('id'));
            this.store.find('pipeline', 1).then(function(pipeline) {
                pipeline.get('nodes').pushObject(unit);
            });
        }
    },

    newUnit: function(munit, name) {
        var res = {};
        res.typeName = munit.get('typeName');
        res.inPorts = munit.get('inPorts');  
        res.outPorts = munit.get('outPorts');
        return res
    }
});

App.UnitController = Ember.ObjectController.extend();

App.nodesController = Ember.ArrayController.create();
