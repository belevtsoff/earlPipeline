import backends.calculator as backend
import os
import time

import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
import tornado.concurrent

from tools import PipelineManager, WebSocketLogHandler

from tornado.options import define, options, parse_command_line

define("port", default=5000, help="run on the given port", type=int)
define("debug", default=True)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


pipelines = PipelineManager()
pipelines.add_pipeline(backend.Pipeline('Ppl1'))
num = backend.Numbers()
lg = backend.ToLog()
pipelines.get_pipeline("Ppl1").add_unit(num, "numnum")
pipelines.get_pipeline("Ppl1").add_unit(lg, "lglg")
pipelines.get_pipeline("Ppl1").connect("numnum", "two", "lglg", "inp")
pipelines.add_pipeline(backend.Pipeline('Ppl2'))

def find_by_attr(seq, attr, value):
    try:
        return filter(lambda item: getattr(item, attr) == value, seq)[0]
    except:
        raise KeyError('%s not found' % value)

## Server RESTfull API

class PipelineHandler(tornado.web.RequestHandler):
    def get(self, pid):
        ppl = pipelines.get_pipeline(pid)
        self.write({'pipeline': ppl.to_dict()})

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

class PipelineEventHandler(tornado.websocket.WebSocketHandler):
    def open(self, pid):
        # add to clients
        self.id = self.get_argument("connId")
        self.ppl = pipelines.get_pipeline(pid)
        clients[self.id] = self

        self.stream.set_nodelay(True)

        self.log_handler = WebSocketLogHandler(self)
        self.ppl.logger.addHandler(self.log_handler)

        print "Stream to %s established" % pid

    def on_message(self, message):
        if message == "RUN":
            print "running %s" % self.ppl.name
            pipelines.start_pipeline(self.ppl.name)
        else:
            print message

    def on_close(self):
        if self.id in clients.keys():
            print "Stream to %s closed" % self.ppl.name
            self.ppl.logger.removeHandler(self.log_handler)
            del clients[self.id]


handlers = [
    (r'/', IndexHandler),
    (r'/api/pipelines/([^/]*)', PipelineHandler),
    (r'/api/pipelines/([^/]*)/units', UnitsHandler),
    (r'/api/pipelines/([^/]*)/edges', EdgesHandler),
    (r'/api/pipelines/([^/]*)/units/([^/]*)', UnitHandler),
    (r'/api/pipelines/([^/]*)/edges/([^/]*)', EdgeHandler),
    (r'/api/metaUnits', MetaUnitsHandler),
    (r'/api/pipelines/([^/]*)/event_bus', PipelineEventHandler)
]

app = tornado.web.Application(handlers,
        debug=options.debug,
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static")
        )

clients = {}

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
