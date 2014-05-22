from flask import Flask, request, render_template, jsonify
from flask.ext.restful import Api, Resource, reqparse
import handlers

app = Flask(__name__)
app.debug=True
api = Api(app)

def resolve_id(d, func):
    if isinstance(d, list):
        for item in d:
            if not item.has_key('id'):
                func(item)
    else:
        func(d)

    return d

def create_id_from_name(d):
    d['id'] = d['name']

def create_edge_id(edge):
    """
    returns a string of a form 'srcId.srcPort->dstId.dstPort'
    """
    edge['id'] = edge['src']+"."+edge['srcPort']+"->"+edge['dst']+"."+edge['dstPort']

def rootify(d, root):
    return {root: d}

def toJSON(d, root, id_func=create_id_from_name):
    #res = resolve_id(d, id_func)
    res = rootify(d, root)
    return jsonify(**res)

parser = reqparse.RequestParser()
parser.add_argument('ids[]', type=str, action='append')

class Pipeline(Resource):
    def get(self, **params):
        ppl_dict = handlers.get_pipeline(params['id'])
        resp = toJSON(ppl_dict, 'pipeline')
        return resp
    #def post(self):
        #print(request.json)
    #def put(self, id):
        #print(request.json)
    #def delete(self, id):
        #print(request.json)

class MetaUnits(Resource):
    def get(self):
        munits = handlers.get_metaUnits()
        resp = toJSON(munits, 'metaUnits')
        return resp


class MetaUnit(Resource):
    def get(self):
        pass

class Units(Resource):
    def get(self):
        args = parser.parse_args()
        units = handlers.get_units(args['ids[]'])
        resp = toJSON(units, 'units')
        return resp

    def post(self):
        unit = request.get_json()['unit']
        return toJSON(handlers.set_unit(unit), 'unit')

class Unit(Resource):
    def get(self):
        pass

class Edges(Resource):
    def get(self):
        args = parser.parse_args()
        edges = handlers.get_edges(args['ids[]'])
        edges = resolve_id(edges, create_edge_id)
        resp = toJSON(edges, 'edges', create_edge_id)
        return resp

class Edge(Resource):
    pass


api.add_resource(Pipeline, '/pipelines/<string:id>')
api.add_resource(Units, '/units')
api.add_resource(Unit, '/units/<string:id>')
api.add_resource(MetaUnits, '/metaUnits')
api.add_resource(MetaUnit, '/metaUnits/<string:id>')
api.add_resource(Edges, '/edges')
api.add_resource(Edge, '/edges/<string:id>')

@app.route('/')
def index():
	return render_template('index.html')

if __name__ == '__main__':
	#db.create_all()
	"""db.session.add(TodoModel("Test"))
	db.session.commit()"""
	app.run()

