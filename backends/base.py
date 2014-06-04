"""
Generic Base classes for modular pipeline interface

If your backend doesn't have it's own graph/dependency resolution system, you
may want to use 'base_simple_engine.py' insted, which implements this API
equipping it with a simple engine
"""

from abc import ABCMeta, abstractmethod, abstractproperty

class GenericUnit(object):
    """
    An abstract base class for unit, a main building block 
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        """Name of this unit instance"""
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


class GenericPipeline(object):
    """This is the base class for 'Pipeline'"""

    __metaclass__ = ABCMeta

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
        Adds connection between two ports

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

    @abstractproperty
    def run(self):
        """Executes the pipeline. Should return the status string,
        containing useful information for the user, or results"""
        pass


# Edge object
class Edge(object):
    """A helper class to encapsulate port naming convention on the front-end"""
    def __init__(self, src, srcPort, dst, dstPort):
        self.src = src
        self.srcPort = srcPort
        self.dst = dst
        self.dstPort = dstPort

    def _get_id(self):
        return self.src+"."+self.srcPort+"->"+self.dst+"."+self.dstPort

    id = property(_get_id)
