# Example backend, which performs simple calculations. It implements
# simple_graph_engine API

from base_simple_engine import Pipeline, Unit, InPort, OutPort

class Numbers(Unit):
    zero = OutPort('zero')
    one = OutPort('one')
    two = OutPort('two')
    three = OutPort('three')
    four = OutPort('four')
    five = OutPort('five')

    def update(self):
        self.zero = 0.0
        self.one = 1.0
        self.two = 2.0
        self.three = 3.0
        self.four = 4.0
        self.five = 5.0

class Div(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def update(self):
        self.res = self.num1 / self.num2

class Add(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def update(self):
        self.res = self.num1 + self.num2

class Mul(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def update(self):
        self.res = self.num1 * self.num2

class Pow(Unit):
    num1 = InPort('num1')
    num2 = InPort('num2')
    res = OutPort('res')

    def update(self):
        self.res = self.num1 ** self.num2

class ToResult(Unit):
    inp = InPort('inp')
    result = OutPort('result')

    def update(self):
        self.result = self.inp


# method, returning types
def get_unit_types():
    return [Numbers, Add, Div, Mul, Pow, ToResult]
