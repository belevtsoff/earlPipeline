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

App.PipelineController = Ember.ObjectController.extend({
    actions: {
        jsPlumbConnect: function(jsPlumbInfo) {
            var edge = this.store.createRecord('edge', {});
            var src = jsPlumbInfo.source.id.split("_");
            var dst = jsPlumbInfo.target.id.split("_");

            this.store.find('unit', src[0]).then(function (unit) {
                edge.set("src", unit);
            });
            this.store.find('unit', dst[0]).then(function (unit) {
                edge.set("dst", unit);
            });

            edge.set("srcPort", src[1]);
            edge.set("dstPort", dst[1]);

            this.get('edges').pushObject(edge);
        }
    },
})

// handlebar helper for initializing connections
// TODO: put it in a better place
Ember.Handlebars.helper("loadConnections", function (edges) {
    for (var i=0; i<edges.length; i++) {
        var src = edges[i].get('src.id');
        var srcPort = edges[i].get('srcPort');
        var dst = edges[i].get('dst.id');
        var dstPort = edges[i].get('dstPort');

        jsPlumb.connect({uuids:[
            src + "_" + srcPort + "_endp",
            dst + "_" + dstPort + "_endp"
        ], editable:true, fireEvent: false});
    }
});
