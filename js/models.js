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
    name: DS.attr('string'),
    inPorts: DS.attr(), // list of strings
    outPorts: DS.attr(), // list of strings
});

App.Unit = DS.Model.extend({
    name: DS.attr('string'),
    type: DS.belongsTo('metaUnit'),
    x: DS.attr('number'),
    y: DS.attr('number'),
});

App.MetaUnit.FIXTURES = [
    {
        id: 1,
        name: 'Generator',
        inPorts: [],
        outPorts: ['out1', 'out2']
    },
    
    {
        id: 2,
        name: 'Dubler',
        inPorts: ['num1'],
        outPorts: ['res']
    },


    {
        id: 3,
        name: 'Adder',
        inPorts: ['num1', 'num2'],
        outPorts: ['res']
    },

    {
        id:4,
        name: "Printer",
        inPorts:['in1', 'in2', 'in3'],
        outPorts:[],
    }
];



App.Unit.FIXTURES = [];
    //{
        //id: 1, typeName: 'Generator',
        //inPorts: [],
        //outPorts: ['out1', 'out2']
    //},
    
    //{
        //id: 2, typeName: 'Dubler',
        //inPorts: ['num1'],
        //outPorts: ['res']
    //},


    //{
        //id: 3, typeName: 'Adder',
        //inPorts: ['num1', 'num2'],
        //outPorts: ['res']
    //},

    //{
        //id:4,
        //typeName: "Printer",
        //inPorts:['in1', 'in2', 'in3'],
        //outPorts:[],
    //}
//];
