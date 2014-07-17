import os

import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
import tornado.concurrent

from tools import PipelineManager, WebSocketLogHandler, LogEventServer
from tornado.options import define, options, parse_command_line

import logging

backend = None
pipelines = None

def find_by_attr(seq, attr, value):
    try:
        return filter(lambda item: getattr(item, attr) == value, seq)[0]
    except:
        raise KeyError('%s not found' % value)

## Server RESTfull API

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class PipelinesHandler(tornado.web.RequestHandler):
    def get(self):
        pplmodels = [ppl.to_dict() for ppl in pipelines]
        self.write({'pipelines':pplmodels})

    def post(self):
        req = tornado.escape.json_decode(self.request.body)['pipeline']
        name = req['id']
        ppl = backend.Pipeline(name)
        pipelines.add_pipeline(ppl)

        self.write({'pipeline': ppl.to_dict()})


class PipelineHandler(tornado.web.RequestHandler):
    def get(self, pid):
        ppl = pipelines.get_pipeline(pid)
        self.write({'pipeline': ppl.to_dict()})

    def delete(self, pid):
        pipelines.remove_pipeline(pid)
        print "deleted %s" % pid
        self.write({})


class MetaUnitsHandler(tornado.web.RequestHandler):
    def get(self):
        munits = [munit.cls_to_dict() for munit in backend.get_unit_types()]
        self.write({'metaUnits': munits})


class UnitsHandler(tornado.web.RequestHandler):
    def get(self, pid):
        ppl = pipelines.get_pipeline(pid)
        units = [unit.to_dict() for unit in ppl.units]
        self.write({'units': units})

    def post(self, pid):
        ppl = pipelines.get_pipeline(pid)
        req = tornado.escape.json_decode(self.request.body)['unit']

        def create_name(ppl, unit_type, counter):
            """Create unit name as lower cased typename plus some number. If
            the name exists in the pipeline, the counter is recursively
            incremented"""
            name = unit_type.lower() + str(counter)
            try:
                find_by_attr(ppl.units, 'name', name)
            except: # no such name
                pass
            else: # if name exists, increment counter
                name = create_name(ppl, unit_type, counter+1)
            finally:
                return name

        cls = find_by_attr(backend.get_unit_types(), '__name__', req['type'])
        unit = cls()

        name = create_name(ppl, req['type'], len(ppl.units))
        ppl.add_unit(unit, name)
        
        self.write({'unit': unit.to_dict()})

class UnitHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def put(self, pid, uid):
        ppl = pipelines.get_pipeline(pid)
        unit = ppl.get_unit(uid)
        req = tornado.escape.json_decode(self.request.body)['unit']
        par_info = unit.parameters_info

        unit.top = req['top']
        unit.left = req['left']

        for par_name, parameter in req['parameters'].items():
            type_func = par_info[par_name]['value_type']
            unit.set_parameter(par_name, type_func(parameter['value']))

        self.write({'unit': unit.to_dict()})

    def delete(self, pid, uid):
        ppl = pipelines.get_pipeline(pid)
        ppl.remove_unit(uid)
        self.write({})


class EdgesHandler(tornado.web.RequestHandler):
    def get(self, pid):
        ppl = pipelines.get_pipeline(pid)
        edges = [edge.to_dict() for edge in ppl.edges]
        self.write({'edges': edges})

    def post(self, pid):
        ppl = pipelines.get_pipeline(pid)
        req = tornado.escape.json_decode(self.request.body)['edge']

        edge = ppl.connect(req['src'], req['srcPort'], req['dst'], req['dstPort'])
        self.write({'edge': edge.to_dict()})
        

class EdgeHandler(tornado.web.RequestHandler):
    def delete(self, pid, eid):
        ppl = pipelines.get_pipeline(pid)
        edge = find_by_attr(ppl.edges, 'id', eid)
        ppl.disconnect(edge.src, edge.srcPort, edge.dst, edge.dstPort)
        self.write({})


class PipelinesEventHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        # add to clients
        self.id = "gui:%s" % self.get_argument("connId")

        self.stream.set_nodelay(True)

        self.log_handler = WebSocketLogHandler(self)
        pipelines.event_server.add_client(self.id, self.log_handler)

        print "Client %s has connected" % self.id

    def on_close(self):
        print "Client %s has disconnected" % self.id
        pipelines.event_server.remove_client(self.id)


class PipelineEventHandler(PipelinesEventHandler):
    def open(self, pid):
        super(PipelineEventHandler, self).open()
        self.ppl = pipelines.get_pipeline(pid)

    def on_message(self, message):
        if message == "RUN":
            print "running %s" % self.ppl.name
            pipelines.start_pipeline(self.ppl.name)
        elif message == "STOP":
            print "stopping %s" % self.ppl.name
            pipelines.stop_pipeline(self.ppl.name)
        elif message == "SAVE":
            print "saving %s" % self.ppl.name
            pipelines.save_pipeline(self.ppl.name)
        else:
            print message


handlers = [
    (r'/', IndexHandler),
    (r'/api/pipelines', PipelinesHandler),
    (r'/api/pipelines/event_bus', PipelinesEventHandler),
    (r'/api/pipelines/([^/]*)', PipelineHandler),
    (r'/api/pipelines/([^/]*)/units', UnitsHandler),
    (r'/api/pipelines/([^/]*)/edges', EdgesHandler),
    (r'/api/pipelines/([^/]*)/units/([^/]*)', UnitHandler),
    (r'/api/pipelines/([^/]*)/edges/([^/]*)', EdgeHandler),
    (r'/api/metaUnits', MetaUnitsHandler),
    (r'/api/pipelines/([^/]*)/event_bus', PipelineEventHandler)
]


# Convenience python API

def run(port=5000, address='', debug=True, pipeline_folder='pipelines'):
    if not backend:
        raise Exception("Cannot start the server: backend is not set. Use 'set_backend' method to set the backend before running the server")

    define("port", default=port, help="run on the given port", type=int)
    define("debug", default=debug)

    app = tornado.web.Application(handlers,
            debug=options.debug,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static")
            )

    event_server = LogEventServer()

    global pipelines
    pipelines = PipelineManager(event_server, pipeline_folder)

    logging.info('starting server')

    parse_command_line()
    app.listen(options.port, address)
    tornado.ioloop.IOLoop.instance().start()

def set_backend(new_backend):
    global backend

    if backend:
        raise Exception("Backend is already set")

    backend = new_backend

if __name__ == '__main__':
    raise Exception("This server is not designed to be run standalone. You should import and set it up in a separate script. For further details, refer to the documentation")
