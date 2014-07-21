// id is used instead of names

App.Pipeline = DS.Model.extend({
    nodes: DS.hasMany('unit', {async: true}),
    edges: DS.hasMany('edge', {async: true}),
    status: DS.attr('string'),
    log: DS.attr(),

    // abusing ember-data to make renaming easy. When persisting a record,
    // ember-data doesn't send the new record's id, so one has to use
    // additional field to convey that information to the server
    old_name: DS.attr('string'), 
});

App.Edge = DS.Model.extend({
    src: DS.belongsTo('unit'),
    srcPort: DS.attr('string'), // port instances are not stored
    dst: DS.belongsTo('unit'),
    dstPort: DS.attr('string'),

    // remove record from cache, if server refused the 'connect' action
    becameError: function(record) {
        record.unloadRecord();
    },

    pipeline: DS.belongsTo('pipeline'),
});

App.MetaUnit = DS.Model.extend({
    inPorts: DS.attr(), // list of strings
    outPorts: DS.attr(), // list of strings
});

App.Unit = DS.Model.extend({
    type: DS.belongsTo('metaUnit'),
    top: DS.attr('number'),
    left: DS.attr('number'),
    status: DS.attr('string'),
    //pipeline: DS.belongsTo('pipeline'),
    
    // Unit settings. This field is expected to be a JSON data of the form:
    //
    // {
    //    name: parameter's name,
    //    type: one of the known to frontend types,
    //    value: value of the parameter,
    //    args: {  # custom arguments, relevant to this type
    //              arg_name: arg_value,
    //              ...
    //          }
    // }
    parameters: DS.attr(null, {defaultValue:
        function() {
            return [{
                name: 'dropdownPar',
                type: 'dropdown',
                value: 'high',
                args: {
                    items: ['low', 'medium','high']
                }
            }, {
                name: 'numberPar',
                type: 'input',
                value: 14.5,
                args: {
                    datatype: 'number',
                },
            }, {
                name: 'boolPar',
                type: 'boolean',
                value: 'false',
            }]
        }
    }),

    becameError: function(record) {
        record.unloadRecord();
    },
});
