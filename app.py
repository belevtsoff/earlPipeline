import backends.calculator as backend
import logging
import multiprocessing as mp
from multiprocessing import Queue
from logutils.queue import QueueHandler
import traceback
import os
import time

import tornado.escape
import tornado.ioloop
import tornado.web

from tornado.options import define, options, parse_command_line

define("port", default=5000, help="run on the given port", type=int)
define("debug", default=True)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

# TODO: make it store and read from disc
# TODO: add docstrings here
# TODO: put it in a separate file
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

handlers = [
    (r'/', IndexHandler),
    (r'/api/pipelines/([^/]*)', PipelineHandler),
    (r'/api/pipelines/([^/]*)/units', UnitsHandler),
    (r'/api/pipelines/([^/]*)/edges', EdgesHandler),
    (r'/api/pipelines/([^/]*)/units/([^/]*)', UnitHandler),
    (r'/api/pipelines/([^/]*)/edges/([^/]*)', EdgeHandler),
    (r'/api/metaUnits', MetaUnitsHandler),
]

app = tornado.web.Application(handlers,
        debug=options.debug,
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static")
        )

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
