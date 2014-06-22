from flask import Flask, request, render_template, jsonify, Response
from flask_restful import Api, Resource, reqparse, fields, marshal, marshal_with, abort
import backends.calculator as backend
from functools import wraps
import logging
import time
import json
import multiprocessing as mp
from multiprocessing import Queue
from logutils.queue import QueueHandler
import traceback
from sse import Sse

app = Flask(__name__)
app.debug=True
api = Api(app)
subscribers = []

# TODO: make it store and read from disc
# TODO: add docstrings here
class PipelineManager(object):
    def __init__(self, data_path = 'pipelines'):
        self._pipelines = {}
        self._running_processes = {}

    def add_pipeline(self, ppl):
        h = logging.StreamHandler()
        f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        h.setFormatter(f)
        ppl.logger.addHandler(h)

        self._pipelines[ppl.name] = ppl

    def get_pipeline(self, name):
        return self._pipelines[name]

    def start_pipeline(self, name):
        ppl = self.get_pipeline(name)

        # a wrapper function which will remove the process from
        # 'running_processes' and log the termination message when the pipeline
        # has finished running
        def run_wrapper():
            try:
                ppl.run()
            except:
                status = 'failed'
                msg = traceback.format_exc()
            else:
                status = 'finished'
                msg = None
            finally:
                # remove from running processes
                del self._running_processes[ppl.name]

                # inform the front-end
                ppl.send_status(status, msg)

        p = mp.Process(target=run_wrapper)
        self._running_processes[ppl.name] = p
        ppl.send_status('running', None)
        p.start()

    def stop_pipeline(self, name):
        ppl = self.get_pipeline(name)
        p = self._running_processes[ppl.name]
        p.terminate()
        del self._running_processes[ppl.name]
        ppl.send_status('failed', "Interrupted by user")

    def is_running(self, name):
        if self._running_processes.has_key(name):
            return True
        return False

pipelines = PipelineManager()
pipelines.add_pipeline(backend.Pipeline('Ppl1'))
pipelines.add_pipeline(backend.Pipeline('Ppl2'))

def rootify(root):
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            data = {root: f(*args, **kwargs)}
            return jsonify(data)
        return wrapped_f
    return wrap

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

class MetaUnitPorts(fields.Raw):
    """A hack to marshal over class methods. 'get_unit_types' returns classes,
    and they don't have properties. This field reads calls specified class
    method and converts its return value to list of strings"""
    def format(self, value):
        ports = value()

        # uugh
        return marshal({'p': ports}, {'p': fields.List(fields.String)})['p']

class UnitParameters(fields.Raw):
    def format(self, parameters):
        result = {}

        parameter_fields = {
            'name': fields.String,
            'type': fields.String(attribute='parameter_type'),
        }

        for par_name, item in parameters.items():

            parameter = marshal(item, parameter_fields)
            # TODO: maybe this is too insecure
            parameter['value'] = item['value']
            parameter['args'] = item['parameter_args']

            result[par_name] = parameter

        return result

metaUnit_fields = {
    'id': fields.String(attribute='__name__'),
    'inPorts': MetaUnitPorts(attribute='get_in_ports'),
    'outPorts': MetaUnitPorts(attribute='get_out_ports')
}

unit_fields = {
    'id': fields.String(attribute='name'),
    'type': fields.String(attribute='__class__.__name__'),
    # TODO: figure out where is the bug. For now, just convert the thing to a
    # string
    'parameters': UnitParameters(attribute='parameters_info'),
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
        return pipelines.get_pipeline(params['pid'])

    # Dummy method, so far
    @rootify('pipeline')
    @marshal_with(pipeline_fields)
    def put(self, **params):
        return pipelines.get_pipeline(params['pid'])

class MetaUnits(Resource):
    @rootify('metaUnits')
    @marshal_with(metaUnit_fields)
    def get(self):
        return backend.get_unit_types()


class Units(Resource):
    @rootify('units')
    @marshal_with(unit_fields)
    def get(self, **params):
        ppl = pipelines.get_pipeline(params['pid'])
        return ppl.units

    @rootify('unit')
    @marshal_with(unit_fields)
    def post(self, **params):
        ppl = pipelines.get_pipeline(params['pid'])
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
        ppl = pipelines.get_pipeline(params['pid'])
        unit = ppl.get_unit(params['id'])
        req = request.get_json()['unit']
        par_info = unit.parameters_info

        unit.top = req['top']
        unit.left = req['left']

        for par_name, parameter in req['parameters'].items():
            type_func = par_info[par_name]['value_type']
            unit.set_parameter(par_name, type_func(parameter['value']))

        return unit

    def delete(self, **params):
        ppl = pipelines.get_pipeline(params['pid'])
        ppl.remove_unit(params['id'])


class Edges(Resource):
    @rootify('edges')
    @marshal_with(edge_fields)
    def get(self, **params):
        ppl = pipelines.get_pipeline(params['pid'])
        return ppl.edges

    @rootify('edge')
    @marshal_with(edge_fields)
    def post(self, **params):
        ppl = pipelines.get_pipeline(params['pid'])
        req = request.get_json()['edge']
        edge = ppl.connect(req['src'], req['srcPort'], req['dst'], req['dstPort'])
        return edge
        

class Edge(Resource):
    def delete(self, **params):
        ppl = pipelines.get_pipeline(params['pid'])
        edge = find_by_attr(ppl.edges, 'id', params['id'])
        ppl.disconnect(edge.src, edge.srcPort, edge.dst, edge.dstPort)

class Launcher(Resource):
    @rootify('result')
    def get(self, **params):
        pipelines.start_pipeline(params['pid'])
        return "OK"

class EventLogger(Resource):
    def get(self, **params):
        ppl = pipelines.get_pipeline(params['pid'])
        q = Queue()
        handler = QueueHandler(q)
        ppl.logger.addHandler(handler)

        def listener():
            try:
                while True:
                    result = q.get()
                    result = result.message
                    ev = Sse()
                    ev.add_message("log", result)
                    yield str(ev)
            except:
                ppl.logger.removeHandler(handler)

        return Response(listener(), mimetype="text/event-stream")
        pass



api.add_resource(Pipelines, '/api/pipelines')
api.add_resource(Pipeline, '/api/pipelines/<string:pid>')
api.add_resource(Launcher, '/api/pipelines/<string:pid>/run')
api.add_resource(EventLogger, '/api/pipelines/<string:pid>/subscribe')

api.add_resource(Units, '/api/pipelines/<string:pid>/units')
api.add_resource(Unit, '/api/pipelines/<string:pid>/units/<string:id>')

api.add_resource(Edges, '/api/pipelines/<string:pid>/edges')
api.add_resource(Edge, '/api/pipelines/<string:pid>/edges/<string:id>')

api.add_resource(MetaUnits, '/api/metaUnits')

@app.route('/')
def index():
	return render_template('index.html')

if __name__ == '__main__':
	#app.run(host="0.0.0.0", port=80)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        app.run(threaded=True)

