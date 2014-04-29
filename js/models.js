App.Pipeline = DS.Model.extend({
    name: DS.attr('string'),
    nodes: DS.hasMany('unit'),
    edges: DS.hasMany('edge')
});

App.Edge = DS.Model.extend({
    src: DS.belongsTo('unit'),
    srcPort: DS.attr('string'), // port instances are not stored
    dst: DS.belongsTo('unit'),
    dstPort: DS.attr('string')
});


App.Pipeline.FIXTURES = 
    [{
        id: 1,
        name: 'Ppl1'
        //nodes: [],
        //edges: []
    }]

App.MetaUnit = DS.Model.extend({
    typeName: DS.attr('string'),
    inPorts: DS.attr(), // list of strings
    outPorts: DS.attr(), // list of strings
});

App.Unit = App.MetaUnit.extend({
    name: DS.attr('string')
});

App.MetaUnit.FIXTURES = [
    {
        id: 1, typeName: 'Generator',
        inPorts: [],
        outPorts: ['number1', 'number2']
    },
    
    {
        id: 2, typeName: 'Dubler',
        inPorts: ['numberIn'],
        outPorts: ['numberOut']
    },


    {
        id: 3, typeName: 'Adder',
        inPorts: ['in1', 'in2'],
        outPorts: ['result']
    },

    {
        id:4,
        typeName: "Printer",
        inPorts:['in1', 'in2', 'in3'],
        outPorts:[],
    }
];

App.Unit.FIXTURES = [];
