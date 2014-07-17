# Example backend, which performs simple calculations. It implements
# simple_graph_engine API

from earlpipeline.backends.base_simple_engine import Pipeline, Unit, InPort, OutPort, Parameter
import time

class Number(Unit):
    out = OutPort('out')
    value = Parameter('value', 'input', float, 5.9, datatype='number')

    def run(self):
        self.out = self.value

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

class Delay(Unit):
    inp = InPort('inp')
    out = OutPort('out')
    delay_sec = Parameter('delay_sec', 'dropdown', int, 3, items=[1, 2, 3, 4, 5])

    def run(self):
        self.out = self.inp
        self.logger.info("waiting %s seconds" % self.delay_sec)
        time.sleep(self.delay_sec)

class ToLog(Unit):
    inp = InPort('inp')

    def run(self):
        self.logger.info("Result: %s" % self.inp)



# method, returning types
def get_unit_types():
    return [Number, Add, Div, Mul, Pow, Failer, Delay, ToLog]
