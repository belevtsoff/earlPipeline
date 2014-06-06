App.Item = Em.View.extend({
  /* ember view setup */
  tagName: 'div',
  classNames: ['unit', 'ui-widget-content'],


  didInsertElement: function () {
    var element = this.get('element');
    var type = this.get('controller').get('type');

    // TODO: avoid the ember-data error for wrong indices
    //if (undefined == type.get('id')) {
        //alert('Something is wrong with the type of "{0}"'
              //.replace("{0}", this.get('controller.name')));
        //this.remove();
        //return
    //}

    this.initElement(element, type);
    console.log(this.get('controller').get('id'));
  },

  // cleanup
  willDestroyElement: function () {
    // TODO: unify this to a single action "sync"
    //this.get('controller').send("savePosition", this.jqel.position());

    for(var i=0; i<this.ports.length; i++) {
        // silently remove all graphic elements associated with the port.
        // No event is fired because we don't wanna delete the edges
        // in the database
        jsPlumb.detachAllConnections(this.ports[i], {fireEvent: false});
        jsPlumb.removeAllEndpoints(this.ports[i], {fireEvent: false});
    }

    // clean-up settings dialogs
    $('#'+this.get('controller.id')+'-settings').remove();
  },
    
  templateName: 'single-unit',

  /* Helper methods */


  initElement: function (element, type) {
    var unit = this.get('controller');
    var inPorts = type.get('inPorts');
    var outPorts = type.get('outPorts');
    this.jqel = $('#'+element.id); // element as jQuery object
    this.ports = []; // helper variable containing all port instances
    var id = this.get('controller.id');
    var dialog_id = id + "-settings";

    // position the element
    
    var top = unit.get('top');
    var left = unit.get('left');

    if(undefined != top && undefined != left) {
        this.jqel.css({
            top: top,
            left: left
        })
    }

    // Create and add ports
    this.appendPorts(inPorts, 'in')
    this.appendPorts(outPorts, 'out')

    // Create settings dialog
    this.appendSettingsDialog(dialog_id);
    

    // EVENT HOOKS
    
    // make draggable
    jsPlumb.draggable(element, {containment: 'parent'});

    // on middle mouse click, delete unit
    this.jqel.on('click', function (event) {
        unit.send('remove');
    });
    
    // subscribe to drop event for position storing
    this.jqel.on('mouseup', function(event) {
        // only on left mouse action
        if (event.which == 1)
            unit.send('savePosition', $(this).position());
    });

    // right click for deletion
    this.jqel.on("contextmenu", function(event) {
        $("#" + dialog_id).dialog("open");
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
        this.jqel.append(container);

        // create and append ports
        for (var i=0; i<ports.length; i++) {
            var port = $('<div></div>')
                .addClass('port')
                .attr({id: App.util.create_port_id(unit_id, ports[i])});
            port.append(ports[i]);

            container.append(port);
            jsPlumb.addEndpoint(port, $.extend({
                uuid: App.util.create_endpoint_id(unit_id, ports[i])
            }, style));

            // store port instance for easier cleanup
            this.ports.pushObject(port);
        };
    },

    /* Creates and appends settings dialog to the body of the page. Created
     * with jQuery UI.
     *
     * @param {string} dialog_id Unique id to be given to the corresponding DOM
     *      element.
     */
    appendSettingsDialog: function (dialog_id) {
        var dialog = $('<div></div>')
            .attr({
                id: dialog_id,
                title: "Settings for \"" + this.get('controller.id') + "\"",
            });

        dialog.append("Settings are not yet implemented");

        $('#body').append(dialog);

        dialog.dialog({
            autoOpen: false,
            modal: true,
        });
    },
});


/* Displays the output of the server, after it has ran the pipeline */
App.OutputView = Ember.View.extend({
    tagName: "aside",
    templateName: "pipeline-output",
});
