# this module has to keep track of all the instances etc. Each handler has to
# return a dictionary. If the dictionary contains no 'id' field, its 'name'
# field will be used as id automatically

ppl = {
        'name': 'Ppl1',
        'nodes': ['someGen', 'someAdd'],
        'edges': [],
        }

edges = [
        {
            'id':1,
            'src': 'someGen',
            'srcPort': 'out1',
            'dst': 'someAdd',
            'dstPort': 'num1',
            'pipeline': 'Ppl1'
        }        
]

metaUnits = [
    {
        'name': 'Generator',
        'inPorts': [],
        'outPorts': ['out1', 'out2']
    },
    
    {
        'name': 'Dubler',
        'inPorts': ['num1'],
        'outPorts': ['res']
    },


    {
        'name': 'Adder',
        'inPorts': ['num1', 'num2'],
        'outPorts': ['res']
    },

    {
        'name': "Printer",
        'inPorts':['in1', 'in2', 'in3'],
        'outPorts':[],
    }
]

units = [
    {
        'type': 'Generator',
        'name': 'someGen',
        'top': 200,
        'left': 200,
    },
    
    {
        'type': 'Dubler',
        'name': 'someDub',
        'top': 300,
        'left': 400,
    },

    {
        'type': 'Adder',
        'name': 'someAdd',
        'top': 120,
        'left': 600,
    },

    {
        'type': 'Printer',
        'name': 'somePrint',
        'top': 200,
        'left': 800,
    },
];

def get_units(ids=None):
    if ids:
        select = []
        for id in ids:
            for u in units:
                if u['name'] == id:
                    select.append(u)
        return select
    else:
        return units

def get_metaUnits():
    return metaUnits

def get_pipelines():
    return [ppl]

def get_edges():
    return edges[0]

def get_pipeline(id):
    return ppl

def get_unit(id):
    pass

def get_metaUnit(id):
    pass

def get_edge(id):
    pass

