// id is used instead of names

App.Pipeline = DS.Model.extend({
    nodes: DS.hasMany('unit', {async: true}),
    edges: DS.hasMany('edge', {async: true})
});

App.Edge = DS.Model.extend({
    src: DS.belongsTo('unit'),
    srcPort: DS.attr('string'), // port instances are not stored
    dst: DS.belongsTo('unit'),
    dstPort: DS.attr('string'),
    //pipeline: DS.belongsTo('pipeline'),
});

App.MetaUnit = DS.Model.extend({
    inPorts: DS.attr(), // list of strings
    outPorts: DS.attr(), // list of strings
});

App.Unit = DS.Model.extend({
    type: DS.belongsTo('metaUnit'),
    top: DS.attr('number'),
    left: DS.attr('number'),
    //pipeline: DS.belongsTo('pipeline'),
});


/* Sample data (for FixtureAdapter) */


//App.MetaUnit.FIXTURES = [
    //{
        //id: 1,
        //name: 'Generator',
        //inPorts: [],
        //outPorts: ['out1', 'out2']
    //},
    
    //{
        //id: 2,
        //name: 'Dubler',
        //inPorts: ['num1'],
        //outPorts: ['res']
    //},


    //{
        //id: 3,
        //name: 'Adder',
        //inPorts: ['num1', 'num2'],
        //outPorts: ['res']
    //},

    //{
        //id:4,
        //name: "Printer",
        //inPorts:['in1', 'in2', 'in3'],
        //outPorts:[],
    //}
//];


//App.Unit.FIXTURES = [
    //{
        //id: 1,
        //type: 1,
        //name: 'someGen',
        //top: 200,
        //left: 200,
    //},
    
    //{
        //id: 2,
        //type: 2,
        //name: 'someDub',
        //top: 300,
        //left: 400,
    //},

    //{
        //id: 3,
        //type: 3,
        //name: 'someAdd',
        //top: 120,
        //left: 600,
    //},

    //{
        //id: 4,
        //type: 4,
        //name: 'somePrint',
        //top: 200,
        //left: 800,
    //},
//];

//App.Pipeline.FIXTURES = [
    //{
        //id: 1,
        //name: 'Ppl1',
        //nodes: [1, 2],
        //edges: []
    //},

    //{
        //id: 2,
        //name: 'Ppl2',
        //nodes: [3],
        //edges: []
    //},

    //{
        //id: 3,
        //name: 'Ppl3',
        //nodes: [4],
        //edges: []
    //},
//];

//App.Edge.FIXTURES = []
