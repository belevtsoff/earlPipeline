"""
Generic Base classes for modular pipeline interface

If your backend doesn't have it's own graph/dependency resolution system, you
may want to use 'base_simple_engine.py' insted, which implements this API
equipping it with a simple engine
"""

from abc import ABCMeta, abstractmethod, abstractproperty
import inspect
import logging
import tools

ROOT_LOG_NAME = "backend"

class GenericUnit(tools.Runnable):
    """
    An abstract base class for unit, a main building block 
    """
    __metaclass__ = ABCMeta

    # API specification

    @abstractproperty
    def name(self):
        """Name of this unit instance"""
        pass

    @abstractproperty
    def pipeline(self):
        """Instance of the pipeline, containing this unit"""
        pass

    @abstractmethod
    def get_in_ports(cls):
        """A class method that should return a list of names of available input
        ports.
        
        IMPORTANT: it HAS to be overloaded with '@classmethod' decorator!"""
        pass

    @abstractmethod
    def get_out_ports(cls):
        """A class method that should return a list of names of available
        output ports
        
        IMPORTANT: it HAS to be overloaded with '@classmethod' decorator!"""
        pass

    @abstractmethod
    def get_parameter(self, name):
        """Getter for a parameter. Unit parameters are exposed via 'Parameter'
        descriptors."""
        pass

    @abstractmethod
    def set_parameter(self, name, value):
        """Setter for a parameter. Unit parameters are exposed via 'Parameter'
        descriptors."""
        pass

    # Partial implementation. These methods should not be normally overloaded.
    # Don't forget to call super(cls, self).__init__() when overloading
    # __init__ of this class

    @property
    def parameters_info(self):
        parameters = {}
        cls = self.__class__
        isparameter = lambda p: issubclass(type(p), Parameter)
        for name, p in inspect.getmembers(cls, isparameter):
            parameters[p.name] = {
                'name': p.name,
                'type': p.parameter_type,
                'value_type': p.value_type, # for internal usage
                'value': getattr(self, p.name),
                'args': p.parameter_args
            }

        return parameters

    @property
    def logger(self):
        """Logger instance for this unit.
        
        Returns
        -------
        logger : Logger
            logger for this unit instance. Its name is of the form
            pipeline_name.unit_name"""

        logger_name = "%s.%s.%s" % (ROOT_LOG_NAME, self.pipeline.name, self.name)
        logger = logging.getLogger(logger_name)
        return logger


    def _on_status_changed(self):
        """Used to send execution status information to the front-end. If
        supported by the back-end implementation, the front-end can update the
        graphical appearance of the units according to their execution status.
        
        Because 'GenericUnit' inherits from Runnable, you don't need to call
        this method explicitly, as it will be invoked automatically when setting
        the 'status' property.
        """
        
        # inform the front-end
        msg = tools.EventTool.create_status_msg(self.status)
        self.logger.info(msg)

    def to_dict(self):
        """Returns a dict, conforming to the 'unit' model definition on the
        front-end (models.js)
        
        Returns
        -------
        res : dict
            JSON-serializable version of this object"""

        # copy
        parameters = dict(self.parameters_info)
        for name, par in parameters.items():
            del par['value_type'] # not for frontend

        res = {
                'id': self.name,
                'type': self.__class__.__name__,
                'parameters': parameters,
                'top': hasattr(self, 'top') and self.top or 100,
                'left': hasattr(self, 'left') and self.left or 100,
                'status': self.status
                }

        return res

    @classmethod
    def cls_to_dict(cls):
        """Returns a dict, conforming to the 'metaUnit' model definition on the
        front-end (models.js)
        
        Returns
        -------
        res : dict
            JSON-serializable version of this class"""

        res = {
                'id': cls.__name__,
                'inPorts': cls.get_in_ports(),
                'outPorts': cls.get_out_ports()
                }

        return res

            

class GenericPipeline(tools.Runnable):
    """This is the base class for 'Pipeline'"""

    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """Name of this pipeline instance"""
        pass

    @abstractproperty
    def units(self):
        """This read-only property should return a list of available
        'GenericUnit' instances in the pipeline"""
        pass

    @abstractproperty
    def edges(self):
        """This read-only property should return a list of available 'Edge'
        instances"""
        pass

    @abstractmethod
    def get_unit(self, unit_name):
        """
        Gets a unit instance by name, if it's in the pipeline.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def remove_unit(self, unit_name):
        """
        Removes specified unit and all its connections

        Parameters
        ----------
        unit_name : str
            name of the unit
        """
        pass

    @abstractmethod
    def connect(self, src_name, src_port, dest_name, dest_port):
        """
        Adds connection between two ports. MUST return Edge instance which was
        just created

        Parameters
        ----------
        src_name : str
            Name of the source unit.
        src_port: str
            Name of the source port.
        dest_name : str
            Name of the destination unit.
        dest_port: str
            Name of the destination port.

        Returns
        -------
        edge: Edge
            edge instance that has just been created
        """
        pass

    @abstractmethod
    def disconnect(self, src_name, src_port, dest_name, dest_port):
        """
        Removes a specified connection, if it is present.

        Parameters
        ----------
        src_name : str
            Name of the source unit.
        src_port: str
            Name of the source port.
        dest_name : str
            Name of the destination unit.
        dest_port: str
            Name of the destination port.
        """
        pass

    @abstractmethod
    def run(self):
        """Executes the pipeline. Should return the status string,
        containing useful information for the user, or results"""
        pass

    # Partial implementation. These methods should not be normally overloaded.
    # Don't forget to call super(cls, self).__init__() when overloading
    # __init__ of this class

    @property
    def logger(self):
        """Logger instance for this pipeline.
        
        Returns
        -------
        logger : Logger
            logger for this pipeline instance. Its name is of the form
            pipeline_name"""

        logger_name = "%s.%s" % (ROOT_LOG_NAME, self.name)
        logger = logging.getLogger(logger_name)
        return logger


    def _on_status_changed(self):
        """Used to send execution status information to the front-end. If
        supported by the back-end implementation, the front-end can update the
        graphical appearance of the elements on the page according to their
        execution status.

        Because 'GenericPipeline' inherits from Runnable, you don't need to call
        this method explicitly, as it will be invoked automatically when setting
        the 'status' property.
        """

        # inform the front-end about status change
        msg = tools.EventTool.create_status_msg(self.status)
        self.logger.info(msg)

    def to_dict(self):
        """Returns a dict, conforming to the 'pipeline' model definition on the
        front-end (models.js)
        
        Returns
        -------
        res : dict
            JSON-serializable version of this object"""

        log = hasattr(self, "_log") and self._log or []

        res = {
                'id': self.name,
                'status': self.status,
                'links' : {
                        'nodes': '/api/pipelines/'+self.name+'/units',
                        'edges': '/api/pipelines/'+self.name+'/edges',
                    },
                'log': log
                }

        return res


# Edge object
class Edge(object):
    """A helper class to encapsulate port naming convention on the front-end"""
    def __init__(self, src, srcPort, dst, dstPort):
        super(Edge, self).__init__()
        self.src = src
        self.srcPort = srcPort
        self.dst = dst
        self.dstPort = dstPort

    def _get_id(self):
        return self.src+"."+self.srcPort+"->"+self.dst+"."+self.dstPort

    id = property(_get_id)

    def to_dict(self):
        """Returns a dict, conforming to the 'edge' model definition on the
        front-end (models.js)
        
        Returns
        -------
        res : dict
            JSON-serializable version of this object"""

        res = {
                'id': self.id,
                'src': self.src,
                'srcPort': self.srcPort,
                'dst': self.dst,
                'dstPort': self.dstPort
                }

        return res


# Parameter descriptor
class Parameter(object):
    """Descriptor class for unit parameter. Is uses abstract methods
    'get_parameter' and 'set_parameter' on the underlying unit instance for
    getting/setting itself."""
    def __init__(self, name, parameter_type, value_type, default_value, **parameter_args):
        """Initialize parameter.

        Parameters
        ----------
        name: str
            Name of the parameter
        parameter_type: str
            Type of the parameter. This field will be sent to the frontend to
            render appropriate input field for this parameter
        value_type: type or callable
            Python type or callable, used to cast the string, returned by the
            frontend, to a valid python type
        default_value: object
            default value of the parameter
        parameter_args: kwargs (value: JSON string)
            Arguments to be passed to the front-end along with the parameter
            type. These arguments are used by front-end to render the
            appropriate input for this parameter. Refer to the frontend
            documentation to see which types are supported and what arguments
            do they require.
        """

        super(Parameter, self).__init__()
        self.name = name
        self.parameter_type = parameter_type
        self.value_type = value_type
        self.default_value = default_value
        self.parameter_args = parameter_args
        self.init_flag_attr = '_%s_initialized' % self.name

    def __get__(self, obj, objtype):
        # for inspection
        if not obj:
            return self

        if not hasattr(obj, self.init_flag_attr):
            setattr(obj, self.init_flag_attr, True)
            obj.set_parameter(self.name, self.default_value)

        return obj.get_parameter(self.name)

    def __set__(self, obj, value):
        obj.set_parameter(self.name, value)
