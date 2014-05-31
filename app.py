from flask import Flask, request, render_template, jsonify
from flask_restful import Api, Resource, reqparse, fields, marshal, marshal_with
import backends.printer as backend
from functools import wraps

app = Flask(__name__)
#app.debug=True
api = Api(app)

pipelines = [backend.Pipeline('Ppl1'), backend.Pipeline('Ppl2')]
#pipelines[0].add_unit(backend.get_unit_types()[0](), 'one')
#pipelines[0].add_unit(backend.get_unit_types()[1](), 'two')
#pipelines[0].connect('one', 'out1', 'two', 'in1')

#def create_id_from_name(d):
    #d['id'] = d['name']

#def create_edge_id(edge):
    #"""
    #returns a string of a form 'srcId.srcPort->dstId.dstPort'
    #"""
    #return edge['src']+"."+edge['srcPort']+"->"+edge['dst']+"."+edge['dstPort']

def rootify(root):
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            data = {root: f(*args, **kwargs)}
            return jsonify(data)
        return wrapped_f
    return wrap

#def toJSON(d, root, id_func=create_id_from_name):
    ##res = resolve_id(d, id_func)
    #res = rootify(d, root)
    #return jsonify(**res)

def find_by_attr(seq, attr, value):
    try:
        return filter(lambda item: getattr(item, attr) == value, seq)[0]
    except:
        raise KeyError('%s not found' % value)

# Herlper structures for automatic object for backend-server API conversion.

class UnitNameField(fields.Raw):
    """Helper class which extracts name field from unit instance
    """
    def format(self, value):
        return marshal(value, {'name': fields.String})['name']

class EdgeIdField(fields.Raw):
    """Helper class which extracts id field from Edge instance
    """
    def format(self, value):
        return marshal(value, {'id': fields.String})['id']

metaUnit_fields = {
    'id': fields.String(attribute='__name__'),
    'inPorts': fields.List(fields.String, attribute='in_ports'),
    'outPorts': fields.List(fields.String, attribute='out_ports')
}

unit_fields = {
    'id': fields.String(attribute='name'),
    'type': fields.String(attribute='__class__.__name__'),
    'top': fields.Integer(default=150),
    'left': fields.Integer(default=150)
}

edge_fields = {
    'id': fields.String,
    'src': fields.String,
    'srcPort': fields.String,
    'dst': fields.String,
    'dstPort': fields.String,
}

pipeline_fields = {
    'id': fields.String(attribute='name'),
    'nodes': fields.List(UnitNameField, attribute='units'),
    'edges': fields.List(EdgeIdField)
}

# Server RESTfull API

class Pipelines(Resource):
    def get(self):
        pass
    def post(self):
        pass

class Pipeline(Resource):
    @rootify('pipeline')
    @marshal_with(pipeline_fields)
    def get(self, **params):
        return find_by_attr(pipelines, 'name', params['pid'])

    # Dummy method, so far
    @rootify('pipeline')
    @marshal_with(pipeline_fields)
    def put(self, **params):
        return find_by_attr(pipelines, 'name', params['pid'])

class MetaUnits(Resource):
    @rootify('metaUnits')
    @marshal_with(metaUnit_fields)
    def get(self):
        return backend.get_unit_types()


class Units(Resource):
    @rootify('units')
    @marshal_with(unit_fields)
    def get(self, **params):
        ppl = find_by_attr(pipelines, 'name', params['pid'])
        return ppl.units

    @rootify('unit')
    @marshal_with(unit_fields)
    def post(self, **params):
        ppl = find_by_attr(pipelines, 'name', params['pid'])
        req = request.get_json()['unit']
        cls = find_by_attr(backend.get_unit_types(), '__name__', req['type'])
        unit = cls()
        ppl.add_unit(unit, req['type'].lower()+str(len(ppl.units)))
        
        return unit

class Unit(Resource):
    def get(self):
        pass
    @rootify('unit')
    @marshal_with(unit_fields)
    def put(self, **params):
        ppl = find_by_attr(pipelines, 'name', params['pid'])
        unit = ppl.get_unit(params['id'])
        req = request.get_json()['unit']

        unit.top = req['top']
        unit.left = req['left']

        return unit

    @rootify('unit')
    @marshal_with(unit_fields)
    def delete(self, **params):
        ppl = find_by_attr(pipelines, 'name', params['pid'])
        unit = ppl.get_unit(params['id'])
        ppl.remove_unit(params['id'])

        return unit
        


class Edges(Resource):
    @rootify('edges')
    @marshal_with(edge_fields)
    def get(self, **params):
        ppl = find_by_attr(pipelines, 'name', params['pid'])
        return ppl.edges

    @rootify('edge')
    @marshal_with(edge_fields)
    def post(self, **params):
        ppl = find_by_attr(pipelines, 'name', params['pid'])
        req = request.get_json()['edge']
        edge = ppl.connect(req['src'], req['srcPort'], req['dst'], req['dstPort'])
        return edge
        

class Edge(Resource):
    #def get(self):
        #pass
    #def put(self):
        #pass
    def delete(self, **params):
        ppl = find_by_attr(pipelines, 'name', params['pid'])
        edge = find_by_attr(ppl.edges, 'id', params['id'])
        ppl.disconnect(edge.src, edge.srcPort, edge.dst, edge.dstPort)

api.add_resource(Pipelines, '/api/pipelines')
api.add_resource(Pipeline, '/api/pipelines/<string:pid>')

api.add_resource(Units, '/api/pipelines/<string:pid>/units')
api.add_resource(Unit, '/api/pipelines/<string:pid>/units/<string:id>')

api.add_resource(Edges, '/api/pipelines/<string:pid>/edges')
api.add_resource(Edge, '/api/pipelines/<string:pid>/edges/<string:id>')

api.add_resource(MetaUnits, '/api/metaUnits')

@app.route('/')
def index():
	return render_template('index.html')

if __name__ == '__main__':
	#db.create_all()
	"""db.session.add(TodoModel("Test"))
	db.session.commit()"""
	app.run()

