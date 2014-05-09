from flask import Flask, request, render_template, jsonify
from flask.ext.restful import Api, Resource, reqparse
import handlers

app = Flask(__name__)
app.debug=True
api = Api(app)

def resolve_id(d):
    def add_id(d):
        if not d.has_key('id'):
            d['id'] = d['name']

    if isinstance(d, list):
        for item in d:
            add_id(item)
    else:
        add_id(d)

    return d

def rootify(d, root):
    return {root: d}

def toJSON(d, root):
    res = resolve_id(d)
    res = rootify(res, root)
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

class Unit(Resource):
    def get(self):
        pass

api.add_resource(Pipeline, '/pipelines/<string:id>')
api.add_resource(Units, '/units')
api.add_resource(Unit, '/units/<string:id>')
api.add_resource(MetaUnits, '/metaUnits')
api.add_resource(MetaUnit, '/metaUnits/<string:id>')
#api.add_resource(Echoe, '/edges/<string:id>')

@app.route('/')
def index():
	return render_template('index.html')

if __name__ == '__main__':
	#db.create_all()
	"""db.session.add(TodoModel("Test"))
	db.session.commit()"""
	app.run()

