//App.PipelinesController = Ember.ArrayController.extend({
    //sortProperties: ['name'],
    //sortAscending: true
//});

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
            unit.save();
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
    //needs: ['pipelines'],
    actions: {
        connect: function(jsPlumbInfo) {
            var edge = this.store.createRecord('edge', {});
            this.updateEdge(edge, jsPlumbInfo);
            this.get('edges').pushObject(edge);
            edge.save();

            // link the edge id to this connection for easy lookup
            jsPlumbInfo.connection.edge_id = edge.get('id');
        },

        disconnect: function(jsPlumbInfo) {
            var id = jsPlumbInfo.connection.edge_id;
            if (undefined != id) {
                this.store.find('edge', id).then(function(edge){
                    edge.deleteRecord();
                    edge.save();
                    //alert('deleted');
                });
            }
            else {
                alert("This connection is not linked to the underlying database");
            }
        },

        move: function(jsPlumbInfo) {
            // On move, disconnect the old thing. The new connection event will
            // be fired automatically
            var id = jsPlumbInfo.connection.edge_id;
            this.send('disconnect', $.extend({
                sourceId: jsPlumbInfo.originalSourceId,
                targetId: jsPlumbInfo.originalTargetId,
            }, jsPlumbInfo));
        }
    },

    updateEdge: function(edge, cntInfo) {
        var src = cntInfo.sourceId.split("_");
        var dst = cntInfo.targetId.split("_");

        this.store.find('unit', src[0]).then(function (unit) {
            edge.set("src", unit);
            //edge.save(); // uugh
        });
        this.store.find('unit', dst[0]).then(function (unit) {
            edge.set("dst", unit);
            //edge.save();
        });

        // this is needed so that if one deletes this edge, the pipeline
        // relations get updated automatically
        edge.set('pipeline', this.get('model'));

        edge.set("srcPort", src[1]);
        edge.set("dstPort", dst[1]);
        //edge.save();
    }
})

// handlebar helper for initializing connections
// TODO: put it in a better place
Ember.Handlebars.helper("loadConnections", function (edges) {
    if(edges) {
        for (var i=0; i<edges.get('content').length; i++) {
            var edge = edges.get('content')[i];
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
});
