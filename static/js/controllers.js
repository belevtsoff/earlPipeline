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
            var ppl = this.get('controllers.pipeline.content');

            // create unit from type
            var unit = this.store.createRecord('unit', {});
            //unit.set('name', munit.get('name')+"-"+unit.get('id'));
            unit.set('type', munit);
            unit.set('pipeline', ppl);

            // sync and add it to the pipeline
            // TODO: handle the server error!
            unit.save().then(function (unit) {
                ppl.get('nodes').addObject(unit);
            });
            
        }
    },
});

App.UnitController = Ember.ObjectController.extend({
    needs: ['pipeline'],
    actions:{
        savePosition: function (position) {
            this.set('model.top', position.top);
            this.set('model.left', position.left);
            this.get('model').save();
        },

        remove: function () {
            var unit = this.get('model');
            var that = this;
            unit.deleteRecord();
            App.currentPipeline.get('nodes').removeObject(unit);
            unit.save().then(function () {
                // reloads edges from the server, because some of them were
                // deleted after the unit was removed
                that.store.unloadAll('edge');
                that.store.find('edge');
            });
        }
    }
});

App.PipelineController = Ember.ObjectController.extend({
    //needs: ['pipelines'],
    actions: {
        /* triggered when two units are manually connected */
        connect: function(jsPlumbInfo) {
            var edge = this.store.createRecord('edge', {});
            var that = this;
            this.updateEdge(edge, jsPlumbInfo)
            .then(function (result) {
                return edge.save();
            })
            .then(function (success) {
                // link the edge id to this connection for easy lookup
                jsPlumbInfo.connection.edge_id = edge.get('id');

                // add relation to pipeline
                that.get('edges').pushObject(edge);

            }, function (error) {
                // in failed, remove the rendered connection
                jsPlumb.detach(jsPlumbInfo.connection, {fireEvent: false});

                // alert the user
                alert("Cannot connect: " + error.responseJSON.message);
                console.log(error);
            });
        },

        /* triggered when two units are manually disconected */
        disconnect: function(jsPlumbInfo) {
            var id = jsPlumbInfo.connection.edge_id;
            if (undefined != id) {
                this.store.find('edge', id)
                .then(function(edge){
                    edge.deleteRecord();
                    return edge.save();
                    //alert('deleted');
                })
                .then(function (success) {
                    // do nothing, everything is fine
                }, function (error, blah) {
                    // This shouldn't fail under normal circumstances! Only
                    // report the error.
                    // TODO: recover the deleted connection and reconnect
                    // jsPlumb
                    alert("Something went wrong, can't disconnect! The error is sent to console")
                });
            }
            else {
                alert("This connection is not linked to the underlying database");
            }
        },

        /* triggered when a connection is moved from one port/unit to another
        * port/unit */
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

        // this is needed so that if one deletes this edge, the pipeline
        // relations get updated automatically
        edge.set('pipeline', this.get('model'));

        edge.set("srcPort", src[1]);
        edge.set("dstPort", dst[1]);

        // create a promise that will be fulfilled after src and dst are found
        // in the database 
        var that = this;
        var lookupPromise = this.store.find('unit', src[0]) //find source
            .then(function (unit) {
                edge.set("src", unit);
                return that.store.find('unit', dst[0]); // then find dst
            }).then(function (unit) {
                edge.set("dst", unit);
            });

        // return the promise
        return lookupPromise
    }
})

// handlebar helper for initializing connections
// TODO: put it in a better place, maybe
Ember.Handlebars.helper("loadConnections", function (edges) {
    if(edges) {
        for (var i=0; i<edges.get('content').length; i++) {
            var edge = edges.get('content')[i];
            App.util.plumbConnect(edge);
        }
    }
});
