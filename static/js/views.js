App.Item = Em.View.extend({
  /* ember view setup */
  tagName: 'div',
  classNames: ['unit', 'ui-widget-content'],


  didInsertElement: function () {
    var element = this.get('element');
    var type = this.get('controller').get('type');

    // TODO: avoid the ember-data error for wrong indices
    if (undefined == type.get('name')) {
        alert('Something is wrong with the type of "{0}"'
              .replace("{0}", this.get('controller.name')));
        this.remove();
        return
    }

    this.initElement(element, type);
    console.log(this.get('controller').get('name'));
  },

  // cleanup
  willDestroyElement: function () {
    // TODO: unify this to a single action "sync"
    this.get('controller').send("savePosition", this.jqel.position());

    for(var i=0; i<this.ports.length; i++) {
        // silently remove all graphic elements associated with the port.
        // No event is fired because we don't wanna delete the edges
        // in the database
        jsPlumb.detachAllConnections(this.ports[i], {fireEvent: false});
        jsPlumb.removeAllEndpoints(this.ports[i], {fireEvent: false});
    }
  },
    
  template: Ember.Handlebars.compile(
      '<h3 class="ui-widget-header">\
        {{view.controller.type.name}}\
      </h3>\
      '),

  /* Helper methods */


  initElement: function (element, type) {
    // TODO: unhardcore port naming convection
    var unit = this.get('controller');
    var inPorts = type.get('inPorts');
    var outPorts = type.get('outPorts');
    this.jqel = $('#'+element.id); // element as jQuery object
    this.ports = []; // helper variable containing all port instances
    var id = this.get('controller.id');


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

    var outPortContainer = $('<div></div>')
        .attr({id:id+'_outputs'})
        .addClass("ports-out");
    var inPortContainer = $('<div></div>')
        .attr({id:id+'_inputs'})
        .addClass("ports-in");

    this.jqel.append(inPortContainer);
    this.jqel.append(outPortContainer);

    /* Add input ports */
    for(var i=0; i<inPorts.length; i++) {
        var port = $('<div></div>')
            .addClass('port')
            .attr({id:id+"_"+inPorts[i]});
        port.append(inPorts[i]);

        inPortContainer.append(port);
        jsPlumb.addEndpoint(port, $.extend({
            uuid: port.attr('id')+"_endp"
        }, drawStyles.targetEndpoint));

        // store port instance for easier cleanup
        this.ports.pushObject(port);
    }

    /* Add output ports */
    for (var i=0; i<outPorts.length; i++) {
        var port = $('<div></div>')
            .addClass('port')
            .attr({id:id+"_"+outPorts[i]});
        port.append(outPorts[i]);

        outPortContainer.append(port);
        jsPlumb.addEndpoint(port, $.extend({
            uuid: port.attr('id')+"_endp"
        }, drawStyles.sourceEndpoint));

        // store port instance for easier cleanup
        this.ports.pushObject(port);
    }
    
    // make draggable
    jsPlumb.draggable(element, {containment: 'parent'});
  }
});
