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
        savePosition: function(position) {
            this.set('model.top', position.top);
            this.set('model.left', position.left);
            this.get('model').save()
            .then(function(success) {
                // everything is fine
            }, function (error) {
                alert("Failed to store element's position. Check out console for details");
                console.log(error);
            });
        },

        saveSettings: function(settings) {
            console.log(settings);
        },

        remove: function() {
            var unit = this.get('model');
            var that = this;
            unit.destroyRecord().then(function () {
                // reloads edges from the server, because 'edges' array of the
                // current pipeline might have changed, because some of edges
                // were deleted after the unit was removed
                App.currentPipeline.get('nodes').removeObject(unit);
                that.store.unloadAll('edge');
                that.store.find('edge');

            }, function(error) {
                alert("Failed to delete unit. Check out console for details");
                console.log(error);
                
                // a workaround to reload previous configuration from server.
                // TODO: handle this nicely internally, without reloading the
                // whole page
                document.location.reload(true);
            });
        }
    }
});

App.PipelineController = Ember.ObjectController.extend({
    //needs: ['pipelines'],
    executionResult: null,
    isRunning: false,

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
                })
                .then(function (success) {
                    // do nothing, everything is fine
                }, function (error) {
                    // This shouldn't fail under normal circumstances! Only
                    // report the error.
                    // TODO: recover the deleted connection and reconnect
                    // jsPlumb
                    alert("Something went wrong, can't disconnect! The error is sent to console");
                    console.log(error);
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
        },
        
        /* Execute the current pipeline and get the data */
        run: function() {
            this.set("isRunning", true);

            // TODO: fix this evil code repetition
            var url = this.store.adapterFor(this).namespace
                + "/pipelines/" + App.currentPipeline.get("id")
                + "/run"
            var that = this;
            $.getJSON(url)
            .then(function(response) {
                that.set("executionResult", response.result);
                that.set("isRunning", false);
            }, function (error) {
                alert("An error occurred: " + error.responseText);
                that.set("isRunning", false);
            });
            //var sleep = function(millis, callback) {
                //setTimeout(function()
                    //{ callback(); } , millis);
            //};
            //var that = this;
            //sleep(1000, function () {
                //that.set("executionResult", "This output is generated on client for testing purposes!!");
                //that.set("isRunning", false);
            //});
        }
    },

    updateEdge: function(edge, cntInfo) {
        var src = App.util.split_port_endp_id(cntInfo.sourceId);
        var dst = App.util.split_port_endp_id(cntInfo.targetId);

        // this is needed so that if one deletes this edge, the pipeline
        // relations get updated automatically
        edge.set('pipeline', this.get('model'));

        edge.set("srcPort", src.port_name);
        edge.set("dstPort", dst.port_name);

        // create a promise that will be fulfilled after src and dst are found
        // in the database 
        var that = this;
        var lookupPromise = this.store.find('unit', src.unit_name) //find source
            .then(function (unit) {
                edge.set("src", unit);
                return that.store.find('unit', dst.unit_name); // then find dst
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
