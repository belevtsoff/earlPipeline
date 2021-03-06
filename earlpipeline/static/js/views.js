App.Item = Em.View.extend({
  /* ember view setup */
  tagName: 'div',
  classNames: ['unit', 'panel', 'panel-success'],
  classNameBindings: ['statusClass'],
  statusClass: 'panel-success',
  statusChanged: function() {
      if(this.get('controller.status') == App.util.status_codes.RUNNING)
          this.set('statusClass', 'panel-warning');
      else if (this.get('controller.status') == App.util.status_codes.FAILED)
          this.set('statusClass', 'panel-danger');
      else
          this.set('statusClass', 'panel-success');
  }.observes('controller.status').on('didInsertElement'),

  didInsertElement: function () {
    // jQuery handle on this element
    this.domElement = $('#' + this.get('element.id'));
    
    // store id in an instance, so that it can be accessed even when the
    // controller is not available
    this.id = this.get('controller.id');

    // TODO: avoid the ember-data error for wrong indices
    //if (undefined == type.get('id')) {
        //alert('Something is wrong with the type of "{0}"'
              //.replace("{0}", this.get('controller.name')));
        //this.remove();
        //return
    //}

    this.initElement();

    // report to the controller that the element has been rendered
    this.get('controller').send('elementRendered', this.get('controller.id'));
  },

  // cleanup
  willDestroyElement: function () {
    // TODO: unify this to a single action "sync"
    //this.get('controller').send("savePosition", this.jqel.position());

    for (var port_type in this.ports) {
        var ports = this.ports[port_type];
        for(var i=0; i<ports.length; i++) {
            // silently remove all graphic elements associated with the port.
            // No event is fired because we don't wanna delete the edges
            // in the database
            jsPlumb.detachAllConnections(ports[i], {fireEvent: false});
            jsPlumb.removeAllEndpoints(ports[i], {fireEvent: false});
        }
    }

    // clean-up settings dialogs
    $('#'+this.id+'-settings').remove();
  },
    
  templateName: 'single-unit',

  /* Helper methods */


  initElement: function () {
    var type = this.get('controller.type');
    var unit = this.get('controller');
    var inPorts = type.get('inPorts');
    var outPorts = type.get('outPorts');
    this.ports = {in: [], out: []}; // helper variable containing all port instances
    var id = this.get('controller.id');
    var dialog_id = id + "-settings";

    // create div for unit content
    this.domBody = $('<div></div>').addClass('panel-body')
    this.domElement.append(this.domBody);

    // position the element
    var top = unit.get('top');
    var left = unit.get('left');

    if(undefined != top && undefined != left) {
        this.domElement.css({
            top: top,
            left: left
        })
    }

    // Create and add ports
    this.appendPorts(inPorts.sort(), 'in')
    this.appendPorts(outPorts.sort(), 'out')

    // Create settings dialog
    this.appendSettingsDialog(dialog_id);
    

    // EVENT HOOKS
    
    // make draggable
    jsPlumb.draggable(this.domElement, {containment: 'parent'});

    // on middle mouse click, delete unit
    this.domElement.on('click', function (event) {
        // only on middle mouse action
        if (event.which == 2)
            unit.send('remove');
    });
    
    // subscribe to drop event for position storing
    this.domElement.on('mouseup', function(event) {
        // only on left mouse action
        if (event.which == 1)
            unit.send('savePosition', $(this).position());
    });

    // right click for settings
    this.domElement.on("contextmenu", function(event) {
        $("#" + dialog_id).modal("show");
    });
  },

  /* Create port container, fill it with ports and append them to current
   * element
   *
   * @param {list of string} ports A list of port names to add
   * @param {string} port_type Ports' type ('in' or 'out')
   * 
   * @returns {Object}
   */
    appendPorts: function (ports, port_type) {
        var unit_id = this.get('controller.id');
        var container = $('<div></div>');
        var style;

        // set container's id and class depending on the port type
        if (port_type == "in") {
            container = container           
                .attr({id:unit_id+'_inputs'})
                .addClass("ports-in");
            style = drawStyles.targetEndpoint;
        }
        else if (port_type == 'out') {
            container = container           
                .attr({id:unit_id+'_outputs'})
                .addClass("ports-out");
            style = drawStyles.sourceEndpoint;
        }

        // append container
        this.domBody.append(container);

        // create and append ports
        for (var i=0; i<ports.length; i++) {
            var port = $('<div></div>')
                .addClass('port')
                .attr({id: App.util.create_port_id(unit_id, ports[i])});
            port.append(ports[i]);

            container.append(port);

            // store port instance for easier cleanup
            this.ports[port_type].pushObject(port);
        };

        // draw port endpoints in a separate loop, after all the port names a
        // printed and the unit has finished adjusting it's width. This
        // prevents wrong alignment of endpoints for output ports.
        for (var i=0; i<ports.length; i++) {
            jsPlumb.addEndpoint(this.ports[port_type][i], $.extend({
                uuid: App.util.create_endpoint_id(unit_id, ports[i])
            }, style));
        };
    },

    /* Creates and appends settings dialog to the body of the page. Created
     * with jQuery UI.
     *
     * @param {string} dialog_id Unique id to be given to the corresponding DOM
     *      element.
     */
    appendSettingsDialog: function(dialog_id) {
        var that = this;

        // Build a bootstrap dialog
        var dialog = new BootstrapDialog({
            title: "Settings for " + this.get('controller.id'),
            message: "", // generated when shown
            id: dialog_id,
            autodestroy: false,

            buttons: [{
                label: 'Ok',
                action: function(dialog) {
                    var form = dialog.getMessage();
                    var par_array = form.serializeArray();

                    // account for and buttons, which should be handled specially
                    var all_params = that.get('controller.parameters');
                    for (var par_name in all_params) {
                        var field = all_params[par_name];
                        if(field.type == 'boolean') {
                            var hasAttr = par_array.findBy('name', field.name);
                            if(!hasAttr)
                                par_array.pushObject(Ember.Object.create({
                                    name: field.name,
                                    value: "off"
                                }));
                        }
                        // source code parameters
                        else if(field.type == 'code') {
                            var code = form.find("[name|='" + field.name + "']")
                                .attr('code');
                            par_array.pushObject(Ember.Object.create({
                                name: field.name,
                                value: code,
                            }));
                        }
                    }

                    // save parameters, if there are any available
                    if (par_array.length > 0) {
                        // grab values from all the fields in the form
                        var parameters = {};
                        $.each(par_array, function(i, field) {
                            switch(field.value) {
                                case "on":
                                    parameters[field.name] = true;
                                    break;
                                case "off":
                                    parameters[field.name] = false;
                                    break;
                                default:
                                    parameters[field.name] = field.value;
                                    break;
                            }
                        });

                        // send the data to the controller for persisting
                        that.get('controller').send('saveSettings', parameters);
                    }

                    dialog.close();
                }
            }, {
                label: 'Cancel',
                action: function(dialog) {
                    dialog.close();
                }
            }],

            onshow: function(dialog) {
                var parameters = that.get('controller.parameters');
                if ($.isEmptyObject(parameters)) {
                    var msg = $("<div />")
                        .append("There are no available parameters for this unit")
                    dialog.setMessage(msg);
                }
                else {
                    dialog.setMessage(that.createForm(parameters));
                }
            }
        });

        dialog.realize();
        $('body').append(dialog.getModal());

    },

    /* Returns a DOM element, which represents a form with all input objects
     * corresponding to a given parameters array.
     *
     * @param {Array} parameters Parameters to generate input for. Each item
     *     object is expected to be of the form, specified in the 'unit' model
     *     description
     *
     * @returns {Object} DOM element
     */
    createForm: function(parameters) {
        // sort parameters by names
        var sorted_names = [];
        for (var par_name in parameters)
            sorted_names[sorted_names.length] = par_name;
        sorted_names.sort();
        
        // Generate the content of the dialog (i.e. parameter settings)
        var form = $('<form />')
            .addClass('form-horizontal')
            .attr({role: 'form'});

        for (var i = 0; i<sorted_names.length; i++) {
            var par_name = sorted_names[i];
            var par_id = this.get('controller.id') + "-parameter-"
                + par_name;

            var group = $('<div />')
                .addClass('form-group');

            var label = $('<label />')
                .attr({for: par_id})
                .addClass('control-label')
                .addClass('col-sm-5')
                .append(par_name);

            var input = $('<div />')
                .addClass('col-sm-5')
                .append(this.createInputElement(parameters[par_name])
                    .attr({id: par_id, name: par_name}));

            group.append(label).append(input).appendTo(form);
        }

        return form
    },

    /* Returns a DOM element, which represents an input DOM object,
     * corresponding to a given type (e.g. dropdown menu for 'dropdown' type),
     * with default values set.
     *
     * If 'type' is unknown, return simple text field
     *
     * @param {Object} parameter Parameter to generate input for. Parameter
     *     object is expected to be of the form, specified in the 'unit' model
     *     description
     *
     * @returns {Object} DOM element
     */
    createInputElement: function(parameter) {
        switch(parameter.type) {
            case 'dropdown':
                return this.createDropdownInput(parameter);
            case 'input':
                return this.createFieldInput(parameter, parameter.args.datatype);
            case 'boolean':
                return this.createCheckboxInput(parameter);
            case 'code':
                return this.createCodeInput(parameter);
            default:
                return this.createFieldInput(parameter, 'text');
        }
    },

    /* Returns a DOM element for a dropdown input, using the contents of the
     * provided 'parameter' argument.
     *
     * @param {Object} parameter Parameter to generate input for. Parameter
     *     object is expected to be of the form, specified in the 'unit' model
     *     description
     *
     * @returns {Object} DOM element for dropdown
     */
    createDropdownInput: function(parameter) {
        var items = parameter.args.items;
        var select = $('<select />')
            .addClass('form-control');

        for (var i = 0; i < items.length; i++) {
            var option = $('<option />', {value: items[i], text: items[i]});
            if (items[i] == parameter.value)
                option.attr({selected: 'selected'});

            option.appendTo(select);
        }

        return select
    },

    /* Returns a DOM element for a text input, using the contents of the
     * provided 'parameter' argument.
     *
     * @param {Object} parameter Parameter to generate input for. Parameter
     *     object is expected to be of the form, specified in the 'unit' model
     *     description
     * @param {String} datatype Specifies what kind of data is to be entered
     *     (e.g. number, text, email, etc.)
     *
     * @returns {Object} DOM element for string
     */
    createFieldInput: function(parameter, datatype) {
        var input = $('<input />')
            .addClass('form-control')
            .attr({
                type: datatype,
                name: parameter.name,
                value: parameter.value,
            });

        return input;
    },


    /* Returns a DOM element for a checkbox input, using the contents of the
     * provided 'parameter' argument.
     *
     * @param {Object} parameter Parameter to generate input for. Parameter
     *     object is expected to be of the form, specified in the 'unit' model
     *     description
     *
     * @returns {Object} DOM element for string
     */
    createCheckboxInput: function(parameter) {
        var input = $('<input />')
            //.addClass('form-control')
            .attr({
                type: 'checkbox',
                name: parameter.name,
            });

        if(parameter.value)
            input.prop('checked', true);
        else
            input.prop('checked', false);

        //return $("<div class='checkbox' />").append(input)
        return input
    },

    /* Returns a DOM element for a source code input. It consist of a button
     * with a hidden source editing dialog which is fired by that button.
     *
     * @param {Object} parameter Parameter to generate input for. This
     *     parameter can contain a field named 'lang' specifying the
     *     programming language for syntax highlighting
     *
     * @returns {Object} DOM element for string
     */
    createCodeInput: function(parameter) {
        var input = $('<button />')
            .addClass('btn btn-default form-control')
            .attr({
                type: "button",
                code: parameter.value,
            })
            .append('Edit source');


        // on button click
        input.click(function(e){
            e.stopPropagation();

            var textarea = $('<textarea />').append(input.attr("code"));

            // create a separate dialog for code editing
            var dialog = new BootstrapDialog({
                title: "Editing Source",
                autodestroy: true,
                message: textarea,
                data: {parameter: parameter},

                onshow: function(dialog) {
                    var lang = dialog.getData('parameter').args.lang;
                    if(!lang)
                        lang = 'python';

                    var editor = CodeMirror.fromTextArea(dialog.getMessage()[0], {
                        mode: lang,
                        lineNumbers: true,
                        matchBrackets: true,
                        autoCloseBrackets: true,
                    });
                    dialog.setData('editorInstance', editor);
                },

                onshown: function(dialog) {
                    var editor = dialog.getData('editorInstance');
                    editor.refresh();
                },

                buttons: [{
                    label: 'Done',
                    action: function(dialog) {
                        var editor = dialog.getData('editorInstance');
                        var code = editor.getValue();
                        input = input.attr({code: code});
                        dialog.close();
                    }
                }, {
                    label: 'Cancel',
                    action: function(dialog) {
                        dialog.close();
                    }
                }],
            });       

            dialog.open();
        });

        return input;
    },
});


/* Displays the output of the server, after it has ran the pipeline */
App.OutputView = Ember.View.extend({
    tagName: "div",
    templateName: "pipeline-output",
    didInsertElement: function() {
        this.scrollBottom();
    },

    scrollBottom: function() {
        var win = $('#logging-window');

        // works correctly only with animation.. weird
        win.animate({
            scrollTop: win[0].scrollHeight+10000,
        }, 10);

    }.observes('controller.log_text'),
});


/* A dialog window to create new pipeline */
App.NewPipelineView = Ember.View.extend({
    tagName: "div",
    didInsertElement: function() {

        var id = "pipeline_name";
        var placeholder = "UnnamedPpl";
        var that = this;
        var title = "Create new pipeline";
        var label = "Pipeline name:";
        
        var ok_callback = function(name) {
            that.get('controller').send('create', name);
        }
        
        var cancel_callback = function() {
            that.get('controller').transitionToRoute('pipelines');
        }
        
        dialog = App.util.input_dialog(id, title, label, placeholder, ok_callback, cancel_callback);
                        

        dialog.open();
    }
})
