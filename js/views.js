App.Item = Em.View.extend({
  /* ember view setup */
  tagName: 'div',
  classNames: ['unit', 'ui-widget-content'],
  didInsertElement: function () {
    var element = this.get('element');



    this.addPorts(element);
    jsPlumb.draggable(element, {containment: 'parent'});
    console.log(element);
    console.log(this.get('content').get('name'));
  },
    
  template: Ember.Handlebars.compile(
      '<h3 class="ui-widget-header">\
        {{view.content.typeName}}\
      </h3>\
      '),

  /* Helper methods */

  addPorts: function (element) {
    /* Adds ports to provided DOM element based on the information provided
    * by the corresponding controller */
    var unit = this.get('content');
    var inPorts = unit.get('inPorts');
    var outPorts = unit.get('outPorts');

    // wourkaround with jQuery
    var jqel = $('#'+element.id);
    var outPortContainer = $('<div></div>')
        .attr({id:element.id+'-outputs'})
        .addClass("ports-out");
    var inPortContainer = $('<div></div>')
        .attr({id:element.id+'-inputs'})
        .addClass("ports-in");

    jqel.append(inPortContainer);
    jqel.append(outPortContainer);

    var spacing = function (i, n) {
        return (i + 1) / (n + 1);
    }

    /* Add input ports */
    for(var i=0; i<inPorts.length; i++) {
        var port = $('<div></div>')
            .addClass('port')
            .attr({id:element.id+inPorts[i]});
        port.append(inPorts[i]);

        var dstpoint = $.extend({
            anchor: [0, 0.5, -1, 0, -4, 0]
        }, drawStyles.targetEndpoint);

        inPortContainer.append(port);
        jsPlumb.addEndpoint(port, dstpoint);
    }

    /* Add output ports */
    for (var i=0; i<outPorts.length; i++) {
        var port = $('<div></div>')
            .addClass('port')
            .attr({id:element.id+outPorts[i]});
        port.append(outPorts[i]);

        var srcpoint = $.extend({
            anchor: [1, 0.5, 1, 0, 4, 0]
        }, drawStyles.sourceEndpoint);

        outPortContainer.append(port);
        jsPlumb.addEndpoint(port, srcpoint);
    }

  }
});

App.PplView = Ember.CollectionView.extend({
  contentBinding: 'App.nodesController',
  itemViewClass: 'App.Item'
});
