//App.PipelinesController = Ember.ArrayController.extend({
    //sortProperties: ['name'],
    //sortAscending: true
//});

App.Runnable = Ember.Mixin.create({
    isRunning: null,
    hasFailed: null,

    statusChanged: function() {
        // using 'if' instead of 'switch' for type conversion
        if (this.get('status') == App.util.status_codes.FINISHED) {
            this.set('isRunning', false);
            this.set('hasFailed', false);
        }
        else if (this.get('status') == App.util.status_codes.RUNNING) {
            this.set('isRunning', true);
            this.set('hasFailed', false);
        }
        else if (this.get('status') == App.util.status_codes.FAILED) {
            this.set('isRunning', false);
            this.set('hasFailed', true);
        }
    }.observes('status'),
});

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

App.UnitController = Ember.ObjectController.extend(App.Runnable, {
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
            var unit = this.get('model');

            for (var par_name in settings) {
                unit.get('parameters.'+par_name).value = settings[par_name];
            }

            unit.save().then(function(success) {
                // all ok
            }, function(error) {
                BootstrapDialog.alert({message: "Failed to store element's parameters. Check out console for details", type: "type-warning"});
                console.log(error);
            });
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

App.PipelineController = Ember.ObjectController.extend(App.Runnable, {
    //needs: ['pipelines'],
    executionResult: "",

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
            this.get("event_bus").send("RUN");
        },

        /* Stop this pipeline, if running */
        stop: function() {
            this.get("event_bus").send("STOP");
        },

        /* Handles a server event, sent via the websocket. The message is
         * supposed to be a JSON-parsable string, of the object of the
         * following forms:
         * 
         * For log msg:
         * {
         *     type: 'log',
         *     content: {
         *         time: log time,
         *         src: {
         *             pipeline: pipeline name,
         *             unit: source unit, or null, if sent from pipeline,
         *         },
         *         msg: message of this event,
         *     }
         * }
         *
         * For status update:
         * {
         *     type: 'status',
         *     content: {
         *         time: log time,
         *         status: new status,
         *         target_type: 'unit' or 'pipeline',
         *         target: name of the target object,
         *     }
         * }
         *
         * The message of each event will be parsed. If the message is of the
         * form "STATUS: status", it will be interpreted as a signal to change
         * running status of a corresponding unit or a pipeline. Other messages
         * will be treated as log messages and will be passed to the results
         * stream */
        handle_server_event: function(data) {
            var event = $.parseJSON(data);
            //var status = App.util.get_status(event.msg)

            // check if this event is status update
            if(event.type == 'status') {
                if (event.content.target_type == 'pipeline') {
                    // update the pipeline's status
                    this.store.update('pipeline', {
                        id: this.get('id'), // this ppl
                        status: event.content.status,
                    });
                    console.log(event.content);
                }
                else if (event.content.target_type == 'unit') {
                    // update the unit's status
                    this.store.update('unit', {
                        id: event.content.target,
                        status: event.content.status,
                    });
                }
            }
            else if(event.type == 'log') {
                msg = App.util.event_to_html(event);
                this.executionResult += msg + "\n";
                console.log(msg);
            }
            
        },
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
