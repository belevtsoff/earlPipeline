"""
Base classes for modular pipeline interface, with a simple graph engine.

Classes 'Unit' and 'Pipeline' implement the generic backend API, specified in
'base.py' and equip the backend with a simple graph engine. These classes
should be used with backends, which don't have their own dependency resolution
and graph management systems. Otherwise, one should implement 'GenericUnit' and
'GenericPipeline' directly.
"""

from earlpipeline.backends.base import GenericUnit, GenericPipeline, Edge, Parameter
from abc import ABCMeta, abstractmethod
from bidict import namedbidict
import inspect
from earlpipeline import tools

UnitMap = namedbidict('UnitMap', 'by_name', 'by_instance')

# TODO: implement optional ports
class Port(object):
    """
    A descriptor class, which is used to abstract away the communication-layer
    machinery from the inner implementation of the 'Unit'. Ports are accessed
    via this descriptor (by instance) from the inside of the unit's
    implementation, and by name (using 'read_port(name)' method) from the
    outside. 

    Parameters
    ----------
    name : str
        name of the port, to be used from the outside
    """
    def __init__(self, name):
        super(Port, self).__init__()
        # TODO: check for name conflicts
        self.name = name

    def __delete__(self, obj):
        raise RuntimeError("Ports can not be deleted. Create a separate class\
                with required port collection")


class OutPort(Port):
    """
    A descriptor class, which is used to abstract away the communication-layer
    machinery from the inner implementation of the 'Unit'. Ports are accessed
    via this descriptor (by instance) from the inside of the unit's
    implementation, and by name (using 'read_port(name)' method) from the
    outside. 

    OutPort descriptor should be written from the inside of the unit's
    implementation to expose required data to other components, which may be
    connected to this port.

    Parameters
    ----------
    name : str
        name of the port, to be used from the outside
    """
    def __get__(self, obj, objtype):
        if obj is None:
            return self

        raise IOError("'OutPort' descriptors are not directly readable by\
                'getattr'. Use the 'read_port(name)' method instead, to access\
                this port by name")       
    
    def __set__(self, obj, value):
        """
        Setter method. Exposes whatever is written to it to outer world via
        the '_output' dictionary of the unit.
        """
        obj._output[self.name] = value


class InPort(Port):
    """
    A descriptor class, which is used to abstract away the communication-layer
    machinery from the inner implementation of the 'Unit'. Ports are accessed
    via this descriptor (by instance) from the inside of the unit's
    implementation, and by name (using 'read_port(name)' method) from the
    outside. 

    InPort descriptor should be read from the inside of the unit's
    implementation to obtain the information, exposed by other unit, connected
    to it.

    Parameters
    ----------
    name : str
        name of the port, to be used from the outside
    """
    def __get__(self, obj, objtype):
        if obj is None:
            return self

        ppl = obj.pipeline
        name = obj.get_name()
        src_unit, src_port = ppl.get_source(name, self.name)
        return ppl.get_unit(src_unit).read_port(src_port)
    
    def __set__(self, obj, value):
        raise IOError("'InPort' descriptors are not writable. Use\
                'Pipeline.connect' to direct data from the OutPort to this\
                port")

# TODO: think on the implementation of Unit's settings
class Unit(GenericUnit):
    """
    An abstract base class for unit, a main building block.

    Unit implements most of the GenericUnit API, so that the user only has to
    implement the 'update' method of the unit
    """
    # API implementation

    @property
    def name(self):
        return self.get_name()

    @classmethod
    def get_in_ports(cls):
        return [name for name, t in cls.get_ports_dict().items()
                if t == "InPort"]

    @classmethod
    def get_out_ports(cls):
        return [name for name, t in cls.get_ports_dict().items()
                if t == "OutPort"]
    
    def _get_pipeline(self):
        if self._pipeline:
            return self._pipeline
        else:
            raise RuntimeError("Unit %s is not in the pipeline" % self)

    # TODO: make sure pipeline is indeed Pipeline
    def _set_pipeline(self, pipeline):
        # do not overwrite pipeline, unless setting it to None
        if self._pipeline is None or pipeline is None:
            self._pipeline = pipeline
        else:
            raise RuntimeError("Unit %s is already in the pipeline %s" %
                    (self.get_name(), self._pipeline))

    pipeline = property(_get_pipeline, _set_pipeline,# _del_pipeline,
            "'Pipeline' instance containing this unit")

    # Main implementation

    def __init__(self):
        super(Unit, self).__init__()
        self._pipeline = None
        self._output = {}

    def get_name(self):
        """
        Obtains the unit's name, if it is contained in the Pipeline

        Returns
        -------
        name : str
        """
        return self.pipeline.get_unit_name(self)

    @abstractmethod
    def run(self):
        """
        Implementation of the unit's inner workings. This method MUST be
        overloaded in the subclasses, otherwise the 'Unit' instance can't be
        created. The implementation should ONLY use the information from the
        available 'InPort's and write ONLY to the available 'OutPort's. The
        implementation should return nothing.
        """
        pass

    def update(self):
        """Wrapper of the user-defined 'run' method, doing all necessary
        actions, e.g. setting running status for this unit"""
        self.status = tools.Status.RUNNING
        try:
            self.run()
        except:
            self.status = tools.Status.FAILED
            # Propagate the error. Traceback message will be sent by the
            # pipeline
            raise
        else:
            self.status = tools.Status.FINISHED

    def read_port(self, name):
        """
        Read the data form OutPort. This method should be used from the outside
        to access data of any available OutPort.

        Parameters
        ----------
        name : str
            Name of the port to read from

        Returns
        -------
        data : object
        """

        self.assert_has_port(name, OutPort)

        # TODO: return caching back, and make it smart
        #if self._output.has_key(name):
            #return self._output[name]
        #else:
        self.update()
        try:
            return self._output[name]
        except:
            raise IOError("The '%s' port's content was never written!"
                    % name)

    @classmethod
    def get_ports_dict(cls):
        """
        Returns a dictionary of all available ports in the form {port_name,
        port_type}

        Returns
        -------
        ports : dict
            {port_name, port_type}
        """

        ports = {}
        isport = lambda p: issubclass(type(p), Port)
        for name, p in inspect.getmembers(cls, isport):
            ports[p.name] = p.__class__.__name__
        
        return ports

    @classmethod
    def assert_has_port(cls, name, port_type=None):
        """
        Tests whether class has a port

        Parameters
        ----------
        name : str
            Name of the port to look up
        port_type : type, optional
            Additionally checks if the port has proper type
        """

        pts = cls.get_ports_dict()
        if pts.has_key(name):
            if not port_type or port_type.__name__ == pts[name]:
                    return True

        raise ValueError("Unit %s doesn't have an OutPort named %s"
                % (cls.__name__, name))

    def get_parameter(self, name):
        return getattr(self, "__" + name)

    def set_parameter(self, name, value):
        setattr(self, "__" + name, value)


class ProcessingUnit(Unit):
    """
    An abstract base class for a processing unit. Processing units are main
    elements of the Pipeline. They come with data_in and data_out ports, and
    are executed sequentially in the Pipeline. 
    """
    data_in = InPort('data_in')
    data_out = OutPort('data_out')


class Connections(object):
    """
    Connection manager class. Holds information about interconnected units and
    ports, and provides methods for their management. This is the base class for
    'Pipeline'.

    Connections implements the GenericPipeline API
    """
    def __init__(self):
        super(Connections, self).__init__()
        self._connections = {}
        self._units = UnitMap()
        self.path_delimiter = '.'

    # Implements necessary abstract properties
    @property
    def units(self):
        return self._units.values()

    @property
    def edges(self):
        edges = []
        for dst_path, src_path in self._connections.items():
            edges.append(self.edge_from_path(src_path, dst_path))

        return edges

    def edge_from_path(self, src_path, dst_path):
        src, src_port = self.split_path(src_path)
        dst, dst_port = self.split_path(dst_path)
        return Edge(src, src_port, dst, dst_port)

    # TODO: do not overwrite if the unit with conflicting name is added,
    # raise exception.
    # TODO: implement naming resolution, in general
    def add_unit(self, unit, unit_name):
        """
        Adds a unit to the pipeline, with specified name

        Parameters
        ----------
        unit : Unit
            An instance of Unit's subclass to be added
        unit_name : str
            name for the added unit. The name has to be unique.
        """
        
        if isinstance(unit, Unit):
            unit.pipeline = self
            self._units.by_name[unit_name] = unit
        else:
            raise TypeError("Only instances of 'Unit' or its subclasses can "
                    "be added; got %s instead" % unit.__class__.__name__)

    def connect(self, src_name, src_port, dest_name, dest_port):
        """
        Adds connection between two ports

        Parameters
        ----------
        src_name : str
            Name of the source unit.
        src_port: str
            Name of the source port. The source port needs to be of the type
            'OutPort'
        dest_name : str
            Name of the destination unit.
        dest_port: str
            Name of the destination port. The destination port needs to be of
            the type 'InPort'

        Returns
        -------
        edge: Edge
            edge instance that has just been created
        """

        src_path = self.make_path(src_name, src_port)
        dest_path = self.make_path(dest_name, dest_port)

        self.assert_valid_path(src_path, OutPort)
        self.assert_valid_path(dest_path, InPort)

        # because an input port can have only one incoming connection, it's
        # convenient to use destination path as a key
        if not self._connections.has_key(dest_path):
            self._connections[dest_path] = src_path
            if not self.is_acyclic():
                self.disconnect(src_name, src_port, dest_name, dest_port)
                raise ValueError("Connection '%s --> %s' creates a cyclic" 
                        " dependency" % (src_path, dest_path))
        else:
            raise ValueError("Input port %s is already connected to some port (%s)"
                    % (dest_path, self._connections[dest_path]))

        return self.edge_from_path(src_path, dest_path)

    def assert_valid_path(self, path, port_type=None):
        """
        Tests if path contains existing unit and port

        Parameters
        ----------
        path : str
            path string in the 'unit_name.port_name' form
        port_type : type, optional
            Additionally checks if the port has proper type
        """

        unit_name, port_name = self.split_path(path)
        unit = self.get_unit(unit_name) # will rise exception if absent 
        unit.assert_has_port(port_name, port_type)

    def assert_has_unit(self, unit_name):
        """
        Tests if Pipeline contains specified unit

        Parameters
        ----------
        unit_name : str
            name of the unit
        """

        try: self._units.by_name[unit_name]
        except KeyError:
            raise ValueError("Pipeline doesn't contain a unit named %s"
                    % unit_name)

    def assert_has_unit_instance(self, unit):
        """
        Tests if Pipeline contains specified (hashable) unit instance

        Parameters
        ----------
        unit : Unit
            unit instance
        """

        try: self._units.by_instance[unit]
        except KeyError:
            raise ValueError("Pipeline doesn't contain a unit instance %s"
                    % unit)

    def is_acyclic(self):
        """
        Checks whether the connections' graph is a Directed Acyclic Graph. A
        topological sorting algorithm is used.
        """
        #import pdb; pdb.set_trace()

        N, E = self.get_unit_graph()

        # find initial nodes
        init_nodes, _ = self.get_init_term_nodes()

        def find_input_set(node):
            I = set()
            for c in E:
                if c[0] == node:
                    I.add(c[1])
            return I

        def find_output_set(node):
            O = set()
            for c in E:
                if c[1] == node:
                    O.add(c[0])
            return O

        # do topological sorting
        L = set()
        while len(init_nodes) > 0:
            n = init_nodes.pop()
            L.add(n)
            for m in find_output_set(n):
                E.remove((m, n))
                if len(find_input_set(m)) == 0:
                    init_nodes.add(m)

        if len(E) > 0:
            return False
        return True

    def get_unit_graph(self):
        """
        Get a set of nodes (units) and a set of edges (ignoring individual
        ports) from the present connection configuration.

        Returns
        -------
        N : set of str
            a set of present nodes (unit names)
        E : set of (dst, src) tuples
            a set of node-node edges, summing up all ports
        """

        N = set(self._units.by_name.keys())
        E = set()
        for dst, src in self._connections.items():
            E.add((self.split_path(dst)[0], self.split_path(src)[0]))
        
        return N, E

    def get_init_term_nodes(self):
        """Get sets of initial (no inputs) and terminal (no outputs) nodes
        
        Returns
        -------
        init_nodes: set of str
            a set of initial nodes (unit names)
        term_nodes: set of str
            a set of terminal nodes (unit names)
        """
        N, E = self.get_unit_graph()

        nodes_with_input = set([conn[0] for conn in E])
        init_nodes = N - nodes_with_input

        nodes_with_output = set([conn[1] for conn in E])
        term_nodes = N - nodes_with_output


        return init_nodes, term_nodes

    def disconnect(self, src_name, src_port, dest_name, dest_port):
        """
        Removes a specified connection, if it is present. Because any input
        port can have only one connection, it's sufficient to supply only the
        destination path to remove the connection.

        Parameters
        ----------
        src_name : str
            This is a dummy argument to comply with generic API
        src_port: str
            This is a dummy argument to comply with generic API
        dest_name : str
            Name of the destination unit.
        dest_port: str
            Name of the destination port. The destination port needs to be of
            the type 'InPort'
        """

        dest_path = self.make_path(dest_name, dest_port)
            
        # make sure there is something to disconnect
        self.get_source(*self.split_path(dest_path))
        del self._connections[dest_path]

    # TODO: don't forget to clean the unit's pipeline property
    def remove_unit(self, unit_name):
        """
        Removes specified unit and all its connections

        Parameters
        ----------
        unit_name : str
            name of the unit
        """
        unit = self.get_unit(unit_name)

        for dest_path, src_path in self._connections.items():
            src_unit, src_port = self.split_path(src_path)
            dest_unit, dest_port = self.split_path(dest_path)

            if src_unit == unit_name or dest_unit == unit_name:
                self.disconnect(src_unit, src_port, dest_unit, dest_port)

        unit.pipeline = None
        del self._units.by_name[unit_name]

    def get_source(self, dest_unit, dest_port):
        """
        Finds, the path to the port, which is connected to 'dest_port'

        Parameters
        ----------
        dest_unit : str
            destination unit
        dest_port : str
            destination port
        """

        dest_path = self.make_path(dest_unit, dest_port)
        self.assert_valid_path(dest_path, InPort)
        if self._connections.has_key(dest_path):
            return self.split_path(self._connections[dest_path])

        raise ValueError("Nothing is connected to %s" % dest_path)

    def get_unit(self, unit_name):
        """
        Gets a unit instance by name, if it's in the pipeline.
        """
        
        self.assert_has_unit(unit_name)
        return self._units.by_name[unit_name]

    def get_unit_name(self, unit):
        """
        Gets unit name, given its (hashable) instance
        """
        self.assert_has_unit_instance(unit)
        return self._units.by_instance[unit]

    def split_path(self, path):
        """
        Splits the path string of the form 'unit.port' into two strings
        """
        
        words = path.split(self.path_delimiter)
        if len(words) == 2:
            return tuple(words)
        
        raise ValueError("'%s' is not a valid path. Use the format: \
                'unit%sport'" % (path, self.path_delimiter))

    def make_path(self, unit_name, port_name):
        """
        Glues unit_name and port_name into a path string using path_delimiter.
        """
        return unit_name + self.path_delimiter + port_name


    def __str__(self):
        res = "Source\t    \tDestination\n"
        res += "------\t    \t-----------\n"

        dest_list = sorted(self._connections.keys())

        for dest in dest_list:
            res+="%s\t<---\t%s\n" % (dest, self._connections[dest])

        return res

class Pipeline(Connections, GenericPipeline):
    """Pipeline class extends 'Connections' to make sure that it contains units
    for reading and writing data, which outline the main data-flow in the
    system."""
    def __init__(self, name='UnnamedPpl'):
        self.name = name
        super(Pipeline, self).__init__()

    # required 'name' property
    def _get_name(self):
        return self._name

    def _set_name(self, val):
        self._name = val

    name = property(_get_name, _set_name)

    def run(self):
        """Calls 'update' methods on all terminal nodes. Terminal
        nodes must take care of writing the results to disk, or
        logging them"""

        _, term_nodes = self.get_init_term_nodes()

        for node_name in term_nodes:
            unit = self.get_unit(node_name)
            unit.update()
