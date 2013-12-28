# A nifty overrides decorator: http://stackoverflow.com/a/8313042
def overrides(interface_class):
    def _overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return _overrider

def trueFalseToOnesAndZeroes(x):
    """ Convert True to 1 and False to 0 """
    if x:
        return 1
    return 0

class GateException(Exception):
    def __init__(self, msg):
        super(GateException, self).__init__(msg)

class Pin(object):
    """ 
    A Pin has a binary value (either True or False). Subclasses should override the setValue() method
    to perform other actions when a value is set.
    """
    def __init__(self):
        self._value = False

    @property
    def value(self):
        return self._value

    @value.setter 
    def value(self, val):
        self.setValue(val)

    def setValue(self, value):
        raise NotImplementedError("Don't instantiate this base class (%s)" % self.__class__.__name__)

class InputPin(Pin):
    """ 
    An InputPin is associated with a particular Gate.
    When an InputPin's value is updated, the pin tells the gate to refresh its output.
    """
    def __init__(self, gate):
        super(InputPin, self).__init__()
        self.gate = gate

    @overrides(Pin)
    def setValue(self, value):
        self._value = bool(value)
        self.gate.refreshOutputs()

class OutputPin(Pin):
    """
    An OutputPin may be connected to other Pins.
    When an OutputPin's value is updated, the pin passes the value along
    to all the pins to which it is connected.
    """
    def __init__(self):
        super(OutputPin, self).__init__()
        self.connections = set()

    @overrides(Pin)
    def setValue(self, value):
        self._value = bool(value)
        for pin in self.connections:
            pin.setValue(self._value)

    def addConnection(self, pin):
        self.connections.add(pin)

class Gate(object):
    """ 
    This defines a base class for logic gates.
    A Gate has a number of input pins and a number of output pins, indexed from 0.
    Inputs and outputs are either True or False.

    Subclasses need to override the refreshOutputs(),
    Subclasses should not need to override the setIn() or getOut() methods.
    """

    def __init__(self, nInputs = 0, nOutputs = 0):
        self._inputs = [InputPin(self) for i in xrange(nInputs)]
        self._outputs = [OutputPin() for i in xrange(nOutputs)]

    @property
    def nInputs(self):
        return len(self._inputs)

    @property
    def nOutputs(self):
        return len(self._outputs)

    def setIn(self, index, value):
        """ Set the given input to bool(value) """
        self.getInPin(index).value = value

    def getOut(self, index):
        """ Get the current value of an output pin """
        self.getOutPin(index).value

    def getInPin(self, index):
        if 0 <= index < len(self._inputs):
            return self._inputs[index]
        raise GateException("No input pin %s on this gate (%s)." % (index, self.__class__.__name__))

    def getOutPin(self, index):
        if 0 <= index < len(self._outputs):
            return self._outputs[index]
        raise GateException("No output pin %s on this gate (%s)." % (index, self.__class__.__name__))

    def setInPin(self, index, pin):
        if 0 <= index < len(self._inputs):
            self._inputs[index] = pin
        else:
            raise GateException("No input pin %s on this gate (%s)." % (index, self.__class__.__name__))

    def setOutPin(self, index, pin):
        if 0 <= index < len(self._outputs):
            self._outputs[index] = pin
        else:
            raise GateException("No output pin %s on this gate (%s)." % (index, self.__class__.__name__))

    def _setOut(self, index, value):
        if 0 <= index < len(self._outputs):
            self._outputs[index].value = value
        else:
            raise GateException("No output pin %s on this gate (%s)." % (index, self.__class__.__name__))

    def refreshOutputs(self):
        """ Reimplement in subclass """
        raise NotImplementedError("Don't instantiate this base class")

    def __str__(self):
        return "%s<In=%s Out=%s>" % (self.__class__.__name__, 
            map(lambda pin: trueFalseToOnesAndZeroes(pin.value), self._inputs),
            map(lambda pin: trueFalseToOnesAndZeroes(pin.value), self._outputs))

    def __repr__(self):
        return str(self)

class And(Gate):
    def __init__(self):
        super(And, self).__init__(2, 1)

    @overrides(Gate)
    def refreshOutputs(self):
        self._setOut(0, all(map(lambda pin: pin.value, self._inputs)))

class Or(Gate):
    def __init__(self):
        super(Or, self).__init__(2, 1)

    @overrides(Gate)
    def refreshOutputs(self):
        self._setOut(0, any(map(lambda pin: pin.value, self._inputs)))

class Not(Gate):
    def __init__(self):
        super(Not, self).__init__(1, 1)

    @overrides(Gate)
    def refreshOutputs(self):
        self._setOut(0, not self._inputs[0].value)

class Xor(Gate):
    def __init__(self):
        super(Xor, self).__init__(2, 1)

    @overrides(Gate)
    def refreshOutputs(self):
        self._setOut(0, self._inputs[0].value ^ self._inputs[1].value)

class TwoGateChain(Gate):
    """ A chain of two gates. """
    def __init__(self, a, b):
        super(TwoGateChain, self).__init__()
        self.a = a
        self.b = b
        if a.nOutputs != b.nInputs:
            raise GateException("Cannot connect %s output pins to %s input pins" % (a.nInputs, b.nOutputs))
        self._inputs.extend(self.a._inputs)
        self._outputs.extend(self.b._outputs)
        for i in xrange(a.nOutputs):
            self.a.getOutPin(i).addConnection(self.b.getInPin(i))

class Nand(TwoGateChain):
    def __init__(self):
        super(Nand, self).__init__(And(), Not())

class Nor(TwoGateChain):
    def __init__(self):
        super(Nor, self).__init__(Or(), Not())

class Xnor(TwoGateChain):
    def __init__(self):
        super(Xnor, self).__init__(Xor(), Not())

def cross_product(x, y): 
    return [[a, b] for a in x for b in y]

def cross(x, size):
    if size <= 1:
        return [[a] for a in x]
    result = cross_product(x, x)
    for n in xrange(size - 2):
        result = [a + [b] for a in result for b in x]
    return result

def enumeratePins(gate):
    for pins in cross([0, 1], gate.nInputs):
        for pin, val in enumerate(pins):
            gate.setIn(pin, val)
        print gate

class Fan(Gate):
    """ Copies a single input to multiple outputs. """
    def __init__(self, nOutputs):
        super(Fan, self).__init__(1, nOutputs)

    @overrides
    def refreshOutputs(self):
        for i in len(self._outputs):
            self._outputs[i].value = self._inputs[0].value

#
# In1------------AND1---|
#                 |     |
#        |---NOT--|     |
# In0---FAN             OR---OUT
#        |-----|        |
#              |        |
# In2---------AND2------|
#
# Here In0 is the selector.
#   In0 = 0 selects In1
#   In0 = 1 selects In2
#
class TwoToOneMux(Gate):
    """ 
    A two-to-one multiplexer. 
    Pins 0 and 1 are the two inputs.
    Pin 2 is the selector:
        Set pin 2 to zero to select pin 0.
        Set pin 2 to one to select pin 1.
    """
    def __init__(self):
        super(TwoToOneMux, self).__init__(3, 1)
        self.twoWayFan = Fan(2)
        self.and1 = And()
        self.and2 = And()
        self.notGate = Not()
        self.orGate = Or()

        # set the input pins
        self.setInPin(0, self.twoWayFan.getInPin(0))
        self.setInPin(1, self.and1.getInPin(0))
        self.setInPin(2, self.and2.getInPin(0))

        # connect encapsulated gates
        self.twoWayFan.getOutPin(0).addConnection(self.notGate.getInPin(0))
        self.twoWayFan.getOutPin(1).addConnection(self.and2.getInPin(1))
        self.notGate.getOutPin(0).addConnection(self.and1.getInPin(1))
        self.and1.getOutPin(0).addConnection(self.orGate.getInPin(0))
        self.and2.getOutPin(0).addConnection(self.orGate.getInPin(1))

        # set the output pins
        self.setOutPin(0, self.orGate.getOutPin)




#
# In0----|
#        OR1----|
# In1----|      |
#               OR3----OUT
# In2----|      |
#        OR2----|
# In3----|
#
class FourWayOr(Gate):
    def __init__(self):
        super(FourWayOr, self).__init__(4, 1)
        self.or1 = Or()
        self.or2 = Or()
        self.or3 = Or()
        self.setInPin(0, self.or1.getInPin(0))
        self.setInPin(1, self.or1.getInPin(1))
        self.setInPin(2, self.or2.getInPin(0))
        self.setInPin(3, self.or2.getInPin(1))
        self.or1.getOutPin(0).addConnection(self.or3.getInPin(0))
        self.or2.getOutPin(0).addConnection(self.or3.getInPin(1))
        self.setOutPin(0, self.or3.getOutPin(0))

if __name__ == '__main__':
    print "--------And gate-------"
    enumeratePins(And())
    print "--------Or gate--------"
    enumeratePins(Or())
    print "--------Not gate-------"
    enumeratePins(Not())
    print "--------Xor gate-------"
    enumeratePins(Xor())
    print "--------Nor gate------"
    enumeratePins(Nor())
    print "--------Nand gate------"
    enumeratePins(Nand())
    print "--------Xnor gate------"
    enumeratePins(Xnor())
    print "--------TwoToOneMux----"
    enumeratePins(TwoToOneMux())
    print "--------FourWayOr------"
    enumeratePins(FourWayOr())

    # nodes = map(lambda x: Node(x), range(4))
    # nodes[0].addChild(nodes[1])
    # nodes[0].addChild(nodes[2])
    # nodes[1].addChild(nodes[2])
    # nodes[1].addChild(nodes[3])
    # nodes[2].addChild(nodes[1])
    # nodes[2].addChild(nodes[3])
    # Node.printGraph(nodes[0])

    # and1 = And()
    # and2 = And()
    # orGate = Or()
    # p = PinConnector()
    # print p
    # p.connect(and1, 0, orGate, 0)
    # p.connect(and2, 0, orGate, 1)
    # print p
    # and1.setIn(0, True)
    # print and1
    # print orGate
    # and1.setIn(1, True)
    # print and1
    # print orGate
