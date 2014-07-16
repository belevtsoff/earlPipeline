import logging
import traceback
import re
import multiprocessing as mp
from logutils.queue import QueueHandler, QueueListener
from functools import wraps
import pickle
import os

class Status(object):
    FINISHED = 1
    RUNNING = 2
    FAILED = 3

    @staticmethod
    def assert_valid(status):
        """checks if this is a valid status. If not, raises a ValueError"""
        istatus = int(status)
        try:
            assert istatus == Status.FINISHED\
                or istatus == Status.RUNNING\
                or istatus == Status.FAILED
        except:
            raise ValueError("Invalid status: %s" % status)


class EventTool(object):
    """This class contains definitions of all special event-types, which are
    supposed to be understood by the front-end. For custom event type,
    implement the static methods '(your_type)_record2dict' and
    'create_(your_type)_msg' for converting your log record to a
    JSON-serializable dict and creating an event msg recpectively."""
    # <EVENT_TYPE:event_data>
    pattern = re.compile("^<([A-Z]*):(.*)>$")
    format_string = "<%s:%s>"

    @staticmethod
    def parse_log_record(record):
        unit = None
        pipeline = None
        srcs = record.name.split(".")

        # srcs[0] is a backend stub
        if len(srcs) == 3:
            pipeline = srcs[1]
            unit = srcs[2]
        elif len(srcs) == 2:
            pipeline = srcs[1]

        # assign parsed attributes
        record.unit, record.pipeline = unit, pipeline

        m = EventTool.pattern.match(record.msg)
        if m:
            event_type, event_data = m.groups()
        else:
            event_type, event_data = "LOG", record.msg

        # assign parsed attributes
        record.event_type, record.event_data = event_type, event_data

        if event_type == "STATUS":
            return EventTool.status_record2dict(record)
        elif event_type == "LOG":
            return EventTool.log_record2dict(record)

    @staticmethod
    def status_record2dict(record):
        status = record.event_data
        if record.pipeline:
            if record.unit:
                target_type = 'unit'
                target = record.unit

            else:
                target_type = 'pipeline'
                target = record.pipeline
            
            res = {
                    'type': 'status',
                    'data': {
                            'time': record.created,
                            'status': status,
                            'target_type': target_type,
                            'target': target
                        }
                    }
            return res
        else:
            # if no pipeline specified, send it as a log event
            return EventTool.log_record2dict(record)

    @staticmethod
    def create_status_msg(status_code):
        """Creates a status message, given the status code"""
        Status.assert_valid(status_code)
        return EventTool.format_string % ("STATUS", status_code)

    @staticmethod
    def log_record2dict(record):
        res = {
                'type': 'log',
                'data': {
                        'time': record.created,
                        'src': {
                            'unit': record.unit,
                            'pipeline': record.pipeline,
                            },
                        'msg': record.msg,
                    }
                }

        return res


class Runnable(object):
    """Adds a 'status' interface to an object, which is writable from other
    processes (uses mp.Value to store status). By design, pipelines are run in
    a separate processes, so this they have to inherit from this class to be
    able to change their status from within the forked environment"""
    def __init__(self):
        self._status = mp.Value('i', Status.FINISHED)
        super(Runnable, self).__init__()

    def _get_status(self):
        return self._status.value

    def _set_status(self, status):
        Status.assert_valid(status)
        self._status.value = int(status)
        self._on_status_changed()

    status = property(_get_status, _set_status)

    def _on_status_changed(self):

        """Optional handler for status change. Overload this if you want to do
        something when status property is changed"""
        pass

    def __getstate__(self):
        """Remove or comvert unpicklabe objects before pickling"""
        __dict__ = dict(self.__dict__) # copy

        # convert synchronized status values to normal integers when pickling
        __dict__['_status'] = self.status

        # ignore some of the auxiliary fields
        # queue_handler
        if __dict__.has_key("queue_handler"):
            del __dict__["queue_handler"]
        # temporary log
        if __dict__.has_key("_log"):
            del __dict__["_log"]

        return __dict__

    def __setstate__(self, state):
        """Restore unpicklable objects when unpickling"""
        self.__dict__.update(state)

        # convert status values back to mp.Value wrappers
        self._status = mp.Value('i', state['_status'])



# TODO: make it store and read from disc
# TODO: add docstrings here
# TODO: put it in a separate file
class PipelineManager(object):
    def __init__(self, event_server, data_path = 'pipelines'):
        # dict {ppl_name : ppl_instance}
        self._pipelines = {}
        self._running_processes = {}

        # create event server and add necessary handlers
        self.event_server = event_server
        self.event_server.start()

        # stopping handler
        stop_handler = CallbackHandler(
                lambda evt: self.pipeline_stopper_callback(evt))
        self.event_server.add_client("PplStopHandler", stop_handler)

        # temporary log callback
        log_handler = CallbackHandler(
                lambda evt: self.pipeline_logger_callback(evt))
        self.event_server.add_client("PplLoggerCallback", log_handler)

        ## debug handler
        #class DebugHandler(logging.Handler):
            #def __init__(self, pplman):
                #super(DebugHandler, self).__init__()
                #self.pplman = pplman

            #def emit(self, record):
                #print record.msg
                #print self.pplman._running_processes
                #print self.pplman.event_server._clients
                #print self.pplman.event_server._pipelines

        #self.event_server.add_client("debugger", DebugHandler(self))

        self.pipelines_folder = 'pipelines'

        for fname in os.listdir(self.pipelines_folder):
            path = os.path.join(self.pipelines_folder, fname)
            if os.path.isfile(path) and path.lower().endswith(".ppl"):
                self.load_pipeline(path)

    def __iter__(self):
        for ppl in self._pipelines.values():
            yield ppl

    def load_pipeline(self, fname):
        with open(fname) as f:
            ppl = pickle.load(f)
        self.add_pipeline(ppl)

    def save_pipeline(self, name):
        fname = os.path.join(self.pipelines_folder, name+".ppl")
        ppl = self.get_pipeline(name)

        with open(fname, 'w') as f:
            pickle.dump(ppl, f)

    def add_pipeline(self, ppl):
        self._pipelines[ppl.name] = ppl
        ppl._log = []

    def get_pipeline(self, name):
        return self._pipelines[name]

    def start_pipeline(self, name):
        ppl = self.get_pipeline(name)

        # clean the object log
        ppl._log = []

        # if hasn't been started before
        # TODO: stupid code
        if not name in self._running_processes.keys():
            self.event_server.add_pipeline(ppl)
        else:
            p = self._running_processes[name]
            if p.is_alive():
                raise Exception("Can't start. The pipeline %s is still running" % name)

        # a wrapper function which logs the termination message when the
        # pipeline has finished running
        def run_wrapper():
            try:
                ppl.logger.info("Starting...")
                ppl.run()
            except:
                status = Status.FAILED
                msg = traceback.format_exc()
            else:
                status = Status.FINISHED
                ppl.logger.info("...done")
                msg = None
            finally:
                # inform the server
                ppl.status = status
                if msg:
                    ppl.logger.error(msg)


        p = mp.Process(target=run_wrapper)
        ppl.status = Status.RUNNING
        p.start()
        self._running_processes[ppl.name] = p

    def stop_pipeline(self, name):
        ppl = self.get_pipeline(name)

        p = self._running_processes[name]
        p.terminate()

        # this will automatically invoke stopping code via stop handler
        ppl.status = Status.FAILED

        ppl.logger.error("Interrupted by user")

    def on_pipeline_stop(self, ppl):
        del self._running_processes[ppl.name]
        self.event_server.remove_pipeline(ppl)
        
    def pipeline_stopper_callback(self, event):
        """Process a parsed log event and call 'on_pipeline_stop', if has
        stopped for some reason"""
        if event['type'] == "status":
            data = event['data']
            if data['target_type'] == 'pipeline':
                name = data['target']
                status = int(data['status'])
                ppl = self.get_pipeline(name)
                if status == Status.FINISHED or status == Status.FAILED:
                    self.on_pipeline_stop(ppl)

    def pipeline_logger_callback(self, event):
        """Stores all pipeline events to a _log entry of a corresponding
        pipeline object"""
        if event['type'] == 'log':
            data = event['data']
            name = data['src']['pipeline']
            if name:
                ppl = self.get_pipeline(name)
                ppl._log.append(data)




def if_running(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.running:
            return f(self, *args, **kwargs)
        else:
            raise Exception(self.__class__.__name__ + " is not running. Start it first.")

    return wrapper

class LogEventServer(object):
    def __init__(self):
        self.queue = mp.Queue()
        self.queue_listener = None
        self._pipelines = {}
        self._clients = {}

    @property
    def running(self):
        return self.queue_listener is not None

    @if_running
    def add_client(self, id, log_handler):
        self._clients[id] = log_handler

        # add handler to a QueueListener
        # TODO: this is bad because all other clients have to wait until this
        # function returns
        self.queue_listener.stop()
        handlers = list(self.queue_listener.handlers)
        handlers.append(log_handler)
        self.queue_listener = QueueListener(self.queue, *handlers)
        self.queue_listener.start()

    @if_running
    def remove_client(self, id):

        log_handler = self._clients[id]
        del self._clients[id]

        self.queue_listener.stop()
        handlers = list(self.queue_listener.handlers)
        handlers.remove(log_handler)
        self.queue_listener = QueueListener(self.queue, *handlers)
        self.queue_listener.start()

    @if_running
    def add_pipeline(self, ppl):
        self._pipelines[ppl.name] = ppl
        ppl.queue_handler = QueueHandler(self.queue)

        # direct messages from this pipeline to the main bus
        ppl.logger.addHandler(ppl.queue_handler)

    @if_running
    def remove_pipeline(self, ppl):
        del self._pipelines[ppl.name]
        
        ppl.logger.removeHandler(ppl.queue_handler)
        del ppl.queue_handler

    def start(self):
        if not self.running:
            self.queue_listener = QueueListener(self.queue)
            self.queue_listener.start()
        else:
            raise Exception("already running")

    @if_running
    def stop(self):
        self.queue_listener.stop()
        self.queue_listener = None


class WebSocketLogHandler(logging.Handler):
    """Packs the received event to a JSON-serializable data format and sends it
    to a client over a given websocket connection """
    def __init__(self, stream):
        """
        Parameters
        ----------
        stream : tornado.websocket.WebSocketHandler
            a websocket connection to send events over
        """
        super(WebSocketLogHandler, self).__init__()
        self.stream = stream

    def emit(self, record):
        res = EventTool.parse_log_record(record)
        self.stream.write_message(res)


class CallbackHandler(logging.Handler):
    """Calls an external function upon log event arrival. The
    callback is invoked with a parsed log record as a
    parameter"""
    def __init__(self, callback):
        super(CallbackHandler, self).__init__()
        self.callback = callback

    def emit(self, record):
        data = EventTool.parse_log_record(record)
        self.callback(data)


