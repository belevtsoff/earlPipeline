App.Item = Em.View.extend({
  /* ember view setup */
  tagName: 'div',
  classNames: ['ui-widget-content', 'unit'],
  didInsertElement: function () {
    var element = this.get('element');
    this.addPorts(element)
    jsPlumb.draggable(element, {containment: 'parent'});
  },
    
  template: Ember.Handlebars.compile('<h3 class="ui-widget-header">{{view.content.typeName}}</h3>'),

  /* Helper methods */

  addPorts: function (element) {
      /* Adds ports to provided DOM element based on the information provided
      * by the corresponding controller */
     var unit = this.get('content');
     var inPorts = unit.get('inPorts');
     var outPorts = unit.get('outPorts');

     var spacing = function (i, n) {
        return (i + 1) / (n + 1);
     }

     /* Add input ports */
     for(var i=0; i<inPorts.length; i++) {
        var dstpoint = $.extend({
            anchor: [0, spacing(i, inPorts.length), -1, 0]
        }, drawStyles.targetEndpoint);

        jsPlumb.addEndpoint(element, dstpoint);
     }

     /* Add output ports */
     for (var i=0; i<outPorts.length; i++) {
        var srcpoint = $.extend({
            anchor: [1, spacing(i, outPorts.length), 1, 0]
        }, drawStyles.sourceEndpoint);

        jsPlumb.addEndpoint(element, srcpoint);
     }
  }
});

App.PplView = Ember.CollectionView.extend({
  contentBinding: 'App.nodesController',
  itemViewClass: 'App.Item'
});
