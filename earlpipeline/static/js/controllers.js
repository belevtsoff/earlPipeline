App.PipelinesController = Ember.ArrayController.extend({
    actions: {
        /* Handles a server event, sent via the websocket. The message is
         * supposed to be a JSON-parsable string, of the object of the
         * following forms:
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
         * Messages of type 'status' will be interpreted as a signal to change
         * running status of a corresponding pipeline. Other messages
         * will be ignored */
        handle_server_event: function(data) {
            var event = $.parseJSON(data);
            
            // handle the event
            switch(event.type) {
                case 'status':
                    this.handle_status_event(event.data);
                    break;
                default:
                    // ignore
                    console.log(event)
                    break;
            }
        },
    },

    handle_status_event: function(data) {
        if (data.target_type == 'pipeline') {
            var ppl = this.get('content').filterBy('id', data.target)[0];
            ppl.set('status', data.status);
        }
    }
});


App.Runnable = Ember.Mixin.create({
    isRunning: null,
    hasFailed: null,

    init: function() {
        this.statusChanged();
    },

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

    renderedUnits: [],
    edgesLoaded: false,

    log_text: "",
    update_log_text: function() {
        var log = this.get('log');
        var tmp = "";
        for(var i=0; i<log.length; i++) 
            tmp += App.util.log_event_to_html(log[i])+"\n"
        this.set('log_text', tmp);
    }.observes('log'),

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
            this.set('log', []); // assuming server does the same
            this.get("event_bus").send("RUN");
        },

        /* Stop this pipeline, if running */
        stop: function() {
            this.get("event_bus").send("STOP");
        },

        save: function() {
            this.get("event_bus").send("SAVE");
        },

        notImplemented: function() {
            alert("This functionality is not yet implemented");
        },

        remove: function() {
            var model = this.get('model');
            var that = this;
            model.deleteRecord();
            model.save().then(function(success) {
                that.transitionToRoute('pipelines');
            }, function(error) {
                BootstrapDialog.alert({message: "Couldn't delete the pipeline. Check out console for details", type: "type-warning"});
                console.log(error.responseText);
            });
        },

        rename: function() {
            var id = "new_pipeline_name";
            var placeholder = "NewName";
            var that = this;
            var title = "Rename pipeline";
            var label = "New pipeline name:";
            
            var callback = function(new_name) {
                var ppl = that.get('model');

                // to understand what's happening in this line, look at
                // pipeline's model definition
                ppl.set("server_flag", "rename");
                ppl.set("old_name", ppl.get('id')); 

                ppl.set("id", new_name); 

                ppl.save().then(function(ppl) {}, function(error) {

                    BootstrapDialog.alert({message: "Couldn't rename the pipeline. Check out console for details", type: "type-warning"});
                console.log(error.responseText);
                });
            }
            
            dialog = App.util.input_dialog(id, title, label, placeholder, callback);
                            

            dialog.open();
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
            
            // handle the event
            switch(event.type) {
                case 'status':
                    this.handle_status_event(event.data);
                    break;
                case 'log':
                    this.handle_log_event(event.data);
                    break;
                default:
                    console.log("Unknown event type " + event.type + " caught:")
                    console.log(event.data)
            }
        },

        // Called by a Unit View, to report that it has been rendered. Once all
        // units are rendered, the 'allUnitsRendered' event is fired. This is
        // done to make sure all units are rendered before connections between
        // them are drawn.
        elementRendered: function(id) {
            console.log('Finished rendering '+id);

            if (!this.edgesLoaded) {
                this.renderedUnits.push(id);

                // TODO: this maybe too slow
                if(this.renderedUnits.length == this.get('nodes.content.length')) {
                    this.send('allUnitsRendered');
                    this.renderedUnits = [];
                }
            }
        },

        // Once all units are rendered, draw connections between them
        allUnitsRendered: function() {
            console.log('all units rendered');
            this.loadConnections();
            this.edgesLoaded = true;
        },
    },

    // Draw connections between units
    loadConnections: function() {
        this.get('edges').then(function(edges) {
            if(edges) {
                for (var i=0; i<edges.get('content').length; i++) {
                    var edge = edges.get('content')[i];
                    App.util.plumbConnect(edge);
                }
            }
        });
    },

    handle_status_event: function(data) {
        if (data.target_type == 'pipeline') {
            // don't persist the change
            this.set('status', data.status);
            console.log(data);
        }
        else if (data.target_type == 'unit') {
            // update the unit's status
            this.store.update('unit', {
                id: data.target,
                status: data.status,
            });
            console.log(data);
        }
    },

    handle_log_event: function(data) {
        // TODO: this can become very slow when the log grows large, fix it
        // somehow
        if(data.src.pipeline == App.currentPipeline.id) {
            var log = this.get('log');
            log.push(data);

            // call manually
            this.update_log_text();
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

// handlebars helper for converting status code into a readable string
Ember.Handlebars.helper("statusToString", function(status_code) {
    if (status_code == App.util.status_codes.FINISHED)
        return "Finished"
    else if (status_code == App.util.status_codes.RUNNING)
        return "Running"
    else if (status_code == App.util.status_codes.FAILED)
        return "Failed"
});
