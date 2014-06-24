import logging
import traceback
import re
import multiprocessing as mp
from logutils.queue import QueueHandler, QueueListener
from functools import wraps

class Status(object):
    FINISHED = 1
    RUNNING = 2
    FAILED = 3
    keyword = "STATUS"
    pattern = re.compile("^%s: (%s|%s|%s)$"
            % (keyword, FINISHED, RUNNING, FAILED))

    @staticmethod
    def create_msg(status):
        """Creates a status message, given the status code"""
        return "%s: %s" % (Status.keyword, status)

    @staticmethod
    def parse_msg(msg):
        """parses status message and returns status-code, or None"""
        m = Status.pattern.match(msg)
        if m:
            return m.groups()[0]
        return m


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

    def _set_status(self, value):
        self._status.value = int(value)

    status = property(_get_status, _set_status)

# TODO: make it store and read from disc
# TODO: add docstrings here
# TODO: put it in a separate file
class PipelineManager(object):
    def __init__(self, event_server, data_path = 'pipelines'):
        # dict {ppl_name : ppl_instance}
        self._pipelines = {}
        self._running_processes = {}

        self.event_server = event_server
        self.event_server.start()

    def add_pipeline(self, ppl):
        self._pipelines[ppl.name] = ppl

    def get_pipeline(self, name):
        return self._pipelines[name]

    def start_pipeline(self, name):
        ppl = self.get_pipeline(name)

        # if hasn't been started before
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
                ppl.run()
            except:
                status = Status.FAILED
                msg = traceback.format_exc()
            else:
                status = Status.FINISHED
                msg = None
            finally:
                # inform the server
                ppl.send_status(status, msg)

        p = mp.Process(target=run_wrapper)
        ppl.send_status(Status.RUNNING, None)
        p.start()
        self._running_processes[ppl.name] = p

    def stop_pipeline(self, name):
        ppl = self.get_pipeline(name)
        p = self._running_processes[name]
        p.terminate()
        del self._running_processes[ppl.name]
        ppl.send_status(Status.FAILED, "Interrupted by user")
        self.event_server.remove_pipeline(ppl)


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
    def add_client(self, client):
        self._clients[client.id] = client

        # add handler to a QueueListener
        # TODO: this is bad because all other clients have to wait until this
        # function returns
        self.queue_listener.stop()
        handlers = list(self.queue_listener.handlers)
        handlers.append(client.log_handler)
        self.queue_listener = QueueListener(self.queue, *handlers)
        self.queue_listener.start()

    @if_running
    def remove_client(self, client):

        del self._clients[client.id]

        self.queue_listener.stop()
        handlers = list(self.queue_listener.handlers)
        handlers.remove(client.log_handler)
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
    def __init__(self, stream):
        super(WebSocketLogHandler, self).__init__()
        self.stream = stream

        # status regexp

    def emit(self, record):
        # check source
        unit = None
        pipeline = None
        srcs = record.name.split(".")


        # srcs[0] is a backend stub
        if len(srcs) == 3:
            pipeline = srcs[1]
            unit = srcs[2]
        elif len(srcs) == 2:
            pipeline = srcs[1]

        # check if it is a status update
        status = Status.parse_msg(record.msg)
        if status and pipeline:
            ppl = self.stream.ppl

            if unit:
                target_type = 'unit'
                target = unit
                ppl.get_unit(unit).status = status

            else:
                target_type = 'pipeline'
                target = pipeline
                ppl.status = status
            
            res = {
                    'type': 'status',
                    'content': {
                            'time': record.created,
                            'status': status,
                            'target_type': target_type,
                            'target': target
                        }
                    }

        else:
            res = {
                    'type': 'log',
                    'content': {
                            'time': record.created,
                            'src': {
                                'unit': unit,
                                'pipeline': pipeline,
                                },
                            'msg': record.msg,
                        }
                    }

        self.stream.write_message(res)
