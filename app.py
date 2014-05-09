from flask import Flask, send_file, request
from flask.ext.restful import Api, Resource

app = Flask(__name__)
app.debug=True
api = Api(app)

class Echop(Resource):
    def get(self, **params):
        print(params)
        return "asdfasdf"
    def post(self):
        print(request.json)
    def put(self, id):
        print(request.json)
    def delete(self, id):
        print(request.json)

class Echou(Echop):
    pass
class Echom(Echop):
    pass
class Echoe(Echop):
    pass

api.add_resource(Echop, '/pipelines/<int:id>')
api.add_resource(Echou, '/units/<int:id>')
api.add_resource(Echom, '/metaUnits/<int:id>')
api.add_resource(Echoe, '/edges/<int:id>')

@app.route('/')
def index():
	return send_file('index.html')

if __name__ == '__main__':
	#db.create_all()
	"""db.session.add(TodoModel("Test"))
	db.session.commit()"""
	app.run()

