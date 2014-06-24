# Example backend, which performs simple calculations. It implements
# simple_graph_engine API

from base_simple_engine import Pipeline, Unit, InPort, OutPort, Parameter
import time

class Numbers(Unit):
    zero = OutPort('zero')
    one = OutPort('one')
    two = OutPort('two')
    three = OutPort('three')
    four = OutPort('four')
    five = OutPort('five')
    int_port = OutPort('int_port')
    flt_port = OutPort('flt_port')

    num1 = Parameter('num1', 'dropdown', int, 12, items=[1, 5, 8, 12, 14])
    num2 = Parameter('num2', 'input', float, 5.9, datatype='number')


    def run(self):
        self.zero = 0.0
        self.one = 1.0
        self.two = 2.0
        self.three = 3.0
        self.four = 4.0
        self.five = 5.0
        self.int_port = self.num1
        self.flt_port = self.num2

class Div(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def run(self):
        self.res = self.num1 / self.num2

class Add(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def run(self):
        self.res = self.num1 + self.num2

class Mul(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def run(self):
        self.res = self.num1 * self.num2

class Pow(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def run(self):
        self.res = self.num1 ** self.num2

class Failer(Unit):
    inp = InPort('inp')
    res = OutPort('res')

    def run(self):
        self.res = self.inp
        raise RuntimeError("Filer failed, as expected...")

class ToLog(Unit):
    inp = InPort('inp')

    def run(self):
        while True:
            time.sleep(10)
            self.logger.info("Result: %s" % self.inp)



# method, returning types
def get_unit_types():
    return [Numbers, Add, Div, Mul, Pow, Failer, ToLog]
