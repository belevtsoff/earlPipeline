# this module has to keep track of all the instances etc. Each handler has to
# return a dictionary. If the dictionary contains no 'id' field, its 'name'
# field will be used as id automatically

pipelines = [{
        'id': 'Ppl1',
        'nodes': ['someGen', 'someAdd'],
        'edges': ['someGen.out1->someAdd.num1'],
        },
        {
        'id': 'Ppl2',
        'nodes': ['someGen', 'someAdd', 'somePrint'],
        'edges': ['someGen.out1->someAdd.num1'],
        }]

edges = [
        {
            'src': 'someGen',
            'srcPort': 'out1',
            'dst': 'someAdd',
            'dstPort': 'num1',
            'pipeline': 'Ppl1'
        }        
]

metaUnits = [
    {
        'id': 'Generator',
        'inPorts': [],
        'outPorts': ['out1', 'out2']
    },
    
    {
        'id': 'Dubler',
        'inPorts': ['num1'],
        'outPorts': ['res']
    },


    {
        'id': 'Adder',
        'inPorts': ['num1', 'num2'],
        'outPorts': ['res']
    },

    {
        'id': "Printer",
        'inPorts':['in1', 'in2', 'in3'],
        'outPorts':[],
    }
]

units = [
    {
        'type': 'Generator',
        'id': 'someGen',
        'top': 200,
        'left': 200,
        'pipeline': "Ppl1"
    },
    
    {
        'type': 'Dubler',
        'id': 'someDub',
        'top': 300,
        'left': 400,
        'pipeline': "Ppl1"
    },

    {
        'type': 'Adder',
        'id': 'someAdd',
        'top': 120,
        'left': 600,
        'pipeline': "Ppl1"
    },

    {
        'type': 'Printer',
        'id': 'somePrint',
        'top': 200,
        'left': 800,
        'pipeline': "Ppl1"
    },
];

def select_items(items, ids, fld='id'):
    if ids:
        select = []
        for id in ids:
            for item in items:
                if item[fld] == id:
                    select.append(item)
        return select
    else:
        return items

def get_units(ids=None):
    return select_items(units, ids)

def get_metaUnits():
    return metaUnits

def get_pipelines():
    return pipelines

def get_edges(ids=None):
    def create_edge_id(edge):
        """
        returns a string of a form 'srcId.srcPort->dstId.dstPort'
        """
        return edge['src']+"."+edge['srcPort']+"->"+edge['dst']+"."+edge['dstPort']

    if ids:
        select = []
        for id in ids:
            for edge in edges:
                if create_edge_id(edge) == id:
                    select.append(edge)
        return select
    else:
        return edges

def get_pipeline(id):
    return filter(lambda p: p['id'] == id, pipelines)[0]

def get_unit(id):
    pass

def get_metaUnit(id):
    pass

def get_edge(id):
    pass

def set_unit(unit):
    unit_id = unit['type']+str(len(units))
    unit['id'] = unit_id
    units.append(unit)
    ppl['nodes'].append(unit['id'])
    return unit

