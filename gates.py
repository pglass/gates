import random

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

    Subclasses need to override the refreshOutputs() method
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
        """ Set the value of an input pin """
        self.getInPin(index).value = value

    def getIn(self, index):
        """ Get the value of an input pin """
        return self.getInPin(index).value

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

def cross(x, size):
    if size <= 1:
        return [[a] for a in x]
    result = [[a, b] for a in x for b in x]
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

    @overrides(Gate)
    def refreshOutputs(self):
        for i in xrange(len(self._outputs)):
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
        self.setOutPin(0, self.orGate.getOutPin(0))


#
# In0----------|
#              AND1---OUT
# In1---|      |
#       AND2---|
# In2---|
#
class ThreeWayAnd(Gate):
    def __init__(self):
        super(ThreeWayAnd, self).__init__(3, 1)
        self.and1 = And()
        self.and2 = And()
        self.setInPin(0, self.and1.getInPin(0))
        self.setInPin(1, self.and2.getInPin(0))
        self.setInPin(2, self.and2.getInPin(1))
        self.and2.getOutPin(0).addConnection(self.and1.getInPin(1))
        self.setOutPin(0, self.and1.getOutPin(0))

#
# In0----|
#        AND1----|
# In1----|       |
#                AND3----OUT
# In2----|       |
#        AND2----|
# In3----|
#
class FourWayAnd(Gate):
    def __init__(self):
        super(FourWayAnd, self).__init__(4, 1)
        self.and1 = And()
        self.and2 = And()
        self.and3 = And()
        self.setInPin(0, self.and1.getInPin(0))
        self.setInPin(1, self.and1.getInPin(1))
        self.setInPin(2, self.and2.getInPin(0))
        self.setInPin(3, self.and2.getInPin(1))
        self.and1.getOutPin(0).addConnection(self.and3.getInPin(0))
        self.and2.getOutPin(0).addConnection(self.and3.getInPin(1))
        self.setOutPin(0, self.and3.getOutPin(0))

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
        # set the input pins
        self.setInPin(0, self.or1.getInPin(0))
        self.setInPin(1, self.or1.getInPin(1))
        self.setInPin(2, self.or2.getInPin(0))
        self.setInPin(3, self.or2.getInPin(1))
        # connect encaspulated gates
        self.or1.getOutPin(0).addConnection(self.or3.getInPin(0))
        self.or2.getOutPin(0).addConnection(self.or3.getInPin(1))
        # set the output pins
        self.setOutPin(0, self.or3.getOutPin(0))



# O indicates wires do not cross
#         In0         In1
#          |           |
#         FAN1-|      FAN2-|
#          |   |       |   |
#          |  NOT1     |  NOT2
#          |   |       |   |
# In2------O---O-------O---O----AND1------|
#          |   |-------O---O----|         |
#          |   |       |   |----|         |
#          |   |       |   |              |
# In3------O---O-------O---O----AND2----| |
#          |   |-------O---O----|       | |
#          |           |---O----|        OR-----OUT
#          |           |   |            | |
# In4------O-----------O---O----AND3----| |
#          |-----------O---O----|         |
#          |           |   |----|         |
#          |           |                  |
# In5------O-----------O--------AND4------|
#          |-----------O--------|
#                      |--------|
class FourToOneMux(Gate):
    """
    A four-to-one multiplexer. 
    Input pins 0 and 1 are the selectors:
        (0, 0) selects input 2
        (0, 1) selects input 3
        (1, 0) selects input 4
        (1, 1) selects input 5
    """
    def __init__(self):
        super(FourToOneMux, self).__init__(6, 1)
        self.fan1 = Fan(2)
        self.fan2 = Fan(2)
        self.not1 = Not()
        self.not2 = Not()
        self.and1 = ThreeWayAnd()
        self.and2 = ThreeWayAnd()
        self.and3 = ThreeWayAnd()
        self.and4 = ThreeWayAnd()
        self.orGate = FourWayOr()

        # set input pins
        self.setInPin(0, self.fan1.getInPin(0))
        self.setInPin(1, self.fan2.getInPin(0))
        self.setInPin(2, self.and1.getInPin(0))
        self.setInPin(3, self.and2.getInPin(0))
        self.setInPin(4, self.and3.getInPin(0))
        self.setInPin(5, self.and4.getInPin(0))

        self.fan1.getOutPin(0).addConnection(self.and3.getInPin(1))
        self.fan1.getOutPin(0).addConnection(self.and4.getInPin(1))
        self.fan1.getOutPin(1).addConnection(self.not1.getInPin(0))

        self.fan2.getOutPin(0).addConnection(self.and2.getInPin(2))
        self.fan2.getOutPin(0).addConnection(self.and4.getInPin(2))
        self.fan2.getOutPin(1).addConnection(self.not2.getInPin(0))

        self.not1.getOutPin(0).addConnection(self.and1.getInPin(1))
        self.not1.getOutPin(0).addConnection(self.and2.getInPin(1))

        self.not2.getOutPin(0).addConnection(self.and1.getInPin(2))
        self.not2.getOutPin(0).addConnection(self.and3.getInPin(2))

        self.and1.getOutPin(0).addConnection(self.orGate.getInPin(0))
        self.and2.getOutPin(0).addConnection(self.orGate.getInPin(1))
        self.and3.getOutPin(0).addConnection(self.orGate.getInPin(2))
        self.and4.getOutPin(0).addConnection(self.orGate.getInPin(3))

        self.setOutPin(0, self.orGate.getOutPin(0))

"""
O indicates wires do not cross
In0  In1
 |    |
 |   FAN2--XOR---OUT1 (sum)
 |    |    |
FAN1--O----|
 |    |    
 |    |----| 
 |         |
 |---------AND---OUT0 (carry)

"""
class HalfAdder(Gate):
    """ A half adder adds two binary digits. """
    def __init__(self):
        super(HalfAdder, self).__init__(2, 2)
        self.fan1 = Fan(2)
        self.fan2 = Fan(2)
        self.xorGate = Xor()
        self.andGate = And()
        self.setInPin(0, self.fan1.getInPin(0))
        self.setInPin(1, self.fan2.getInPin(0))
        
        self.fan1.getOutPin(0).addConnection(self.xorGate.getInPin(0))
        self.fan1.getOutPin(1).addConnection(self.andGate.getInPin(0))
        self.fan2.getOutPin(0).addConnection(self.xorGate.getInPin(1))
        self.fan2.getOutPin(1).addConnection(self.andGate.getInPin(1))

        self.setOutPin(0, self.andGate.getOutPin(0))
        self.setOutPin(1, self.xorGate.getOutPin(0))

"""
i0, i1 are input pins to an internal gate
o0, o1 are output pins from an internal gate

In0---------FAN1-----|      i1
             |       XOR-----************* o1
In1--FAN2----O-------|       * HalfAdder *---------------OUT1 (sum)
      |      |               *           *
In2---O------O---------------*************
      |      |              i0           | o0
      |      |                           |-------|
      |      |------------|                      OR-----OUT0 (carry)
      |                   AND--------------------|
      |-------------------|
"""
class OneBitAdder(Gate):
    """
    A one bit adder can add three bits. Typically, In0 and In1 are the 
    two operands and In2 is a carry bit from a previous operation.

    Out0 is the carry bit and Out1 is the sum bit.
    So the value of the computation is 2*Out0 + Out1.
    """
    def __init__(self):
        super(OneBitAdder, self).__init__(3, 2)
        self.fan1 = Fan(2)
        self.fan2 = Fan(2)
        self.xorGate = Xor()
        self.halfAdder = HalfAdder()
        self.andGate = And()
        self.orGate = Or()

        self.setInPin(0, self.fan1.getInPin(0))
        self.setInPin(1, self.fan2.getInPin(0))
        self.setInPin(2, self.halfAdder.getInPin(0))

        self.fan1.getOutPin(0).addConnection(self.xorGate.getInPin(0))
        self.fan1.getOutPin(0).addConnection(self.andGate.getInPin(0))
        self.fan2.getOutPin(0).addConnection(self.xorGate.getInPin(1))
        self.fan2.getOutPin(0).addConnection(self.andGate.getInPin(1))

        self.xorGate.getOutPin(0).addConnection(self.halfAdder.getInPin(1))

        self.halfAdder.getOutPin(0).addConnection(self.orGate.getInPin(0))
        self.andGate.getOutPin(0).addConnection(self.orGate.getInPin(1))
        self.setOutPin(1, self.halfAdder.getOutPin(1))
        self.setOutPin(0, self.orGate.getOutPin(0))

"""

                 In0   In1              In2   In3              In4   In5             In6   In7
                  |     |                |     |                |     |               |     |
                  |     |                |     |                |     |               |     |
                  |i0   |i1              |i0   |i1              |i0   |i1             |i0   |i1
              ****************       ****************       ****************      ****************
In8-----------* OneBitAdder1 *-------* OneBitAdder2 *-------* OneBitAdder3 *------* OneBitAdder4 *-----OUT4
            i2****************o0   i2****************o0   i2****************o0  i2****************o0
                    |o1                    |o1                    |o1                   |o1   
                    |                      |                      |                     |
                    OUT0                   OUT1                   OUT2                  OUT3
"""
class FourBitAdder(Gate):
    """ 
    A FourBitAdder can add two four-bit numbers and a one-bit carry.
    That is, it adds the following:
              In6  In4  In2  In0
            + In7  In5  In3  In1
            +                In8
        ------------------------
        Out4 Out3 Out2 Out1 Out0
    """
    def __init__(self):
        super(FourBitAdder, self).__init__(9, 5)
        self.oneBitAdder1 = OneBitAdder()
        self.oneBitAdder2 = OneBitAdder()
        self.oneBitAdder3 = OneBitAdder()
        self.oneBitAdder4 = OneBitAdder()

        self.setInPin(0, self.oneBitAdder1.getInPin(0))
        self.setInPin(1, self.oneBitAdder1.getInPin(1))
        self.setInPin(2, self.oneBitAdder2.getInPin(0))
        self.setInPin(3, self.oneBitAdder2.getInPin(1))
        self.setInPin(4, self.oneBitAdder3.getInPin(0))
        self.setInPin(5, self.oneBitAdder3.getInPin(1))
        self.setInPin(6, self.oneBitAdder4.getInPin(0))
        self.setInPin(7, self.oneBitAdder4.getInPin(1))
        self.setInPin(8, self.oneBitAdder1.getInPin(2))

        self.oneBitAdder1.getOutPin(0).addConnection(self.oneBitAdder2.getInPin(2))
        self.oneBitAdder2.getOutPin(0).addConnection(self.oneBitAdder3.getInPin(2))
        self.oneBitAdder3.getOutPin(0).addConnection(self.oneBitAdder4.getInPin(2))

        self.setOutPin(0, self.oneBitAdder1.getOutPin(1))
        self.setOutPin(1, self.oneBitAdder2.getOutPin(1))
        self.setOutPin(2, self.oneBitAdder3.getOutPin(1))
        self.setOutPin(3, self.oneBitAdder4.getOutPin(1))
        self.setOutPin(4, self.oneBitAdder4.getOutPin(0))

    def __str__(self):
        return "%s<A=%s B=%s c=%s OUT=%s>" % (
            self.__class__.__name__, 
            map(lambda pin: trueFalseToOnesAndZeroes(pin.value), [self._inputs[i] for i in [6,4,2,0]]),
            map(lambda pin: trueFalseToOnesAndZeroes(pin.value), [self._inputs[i] for i in [7,5,3,1]]),
            trueFalseToOnesAndZeroes(self._inputs[8].value),
            map(lambda pin: trueFalseToOnesAndZeroes(pin.value), reversed(self._outputs))
        )

"""
o0 indicates the output of an internal gate
               o0
(Q) OUT0----+----NOR---In0 (reset)
            |      |
            |      |
(set) In1---NOR----+---OUT1 (not Q)
               o0
"""
class SRLatch(Gate):
    """
    This is a simple memory circuit that can store one bit.

    An SRLatch has two inputs:
        In0 is the reset line
        In1 is the set line
    There are two output lines, but OUT1 is low when OUT0 is high and (vice versa)

    When In0 and In1 are both False, the outputs remain as they were.
    When In0 is True and In1 False, we "reset" the memory:
        OUT0 becomes False and OUT1 becomes True
        If In0 becomes False, these outputs stay the same.
    When In0 is False and In1 is True, we "set" the memory:
        OUT0 becomes True and OUT1 becomes False.
        If In1 subsequently returns to False, the outputs remain the same due to the feedback loop.
    If In0 and In1 are both True, then a race condition occurs.
        The output is undefined in this case.

    NOTE: The feedback loop results in infinite recursion, so this is not implemented 
    in terms of other gates.
    """

    def __init__(self):
        super(SRLatch, self).__init__(2, 2)
        self._setOut(0, False)
        self._setOut(1, True)

    @overrides(Gate)
    def refreshOutputs(self):
        R = self.getIn(0)
        S = self.getIn(1)
        if R and S:         # when both inputs are high a race condition occurs
            x = bool(random.randint(1, 10) % 2)
            self._setOut(0, x)
            self._setOut(1, not x)
        elif R and not S:   # reset
            self._setOut(0, False)
            self._setOut(1, True)
        elif not R and S:   # set
            self._setOut(0, True)
            self._setOut(1, False)
        # otherwise, R and S both False, so output remains unchanged.


"""
(R) In0-----AND1--|   i0         o0
            |     |----***********--------OUT0 (Q)
(E) In2----FAN         * SRLatch *
            |     |----***********--------OUT1 (not Q)
(S) In1-----AND2--|    i1        o1
"""
class GatedSRLatch(Gate):
    """
    This is an SR-latch with an "enable" line.
    The latch cannot be set or reset when the enable line is low.

    In0 is the "reset" line.
    In1 is the "set" line.
    In2 is the "enable" line.

    When the enable line is True, this is equivalent to an SRLatch.
    When the enable line is False, the reset and set lines are turned off (both become False)
    """
    def __init__(self):
        super(GatedSRLatch, self).__init__(3, 2)
        self.fan = Fan(2)
        self.and1 = And()
        self.and2 = And()
        self.latch = SRLatch()

        self.setInPin(0, self.and1.getInPin(0))
        self.setInPin(1, self.and2.getInPin(0))
        self.setInPin(2, self.fan.getInPin(0))

        self.fan.getOutPin(0).addConnection(self.and1.getInPin(1))
        self.fan.getOutPin(1).addConnection(self.and2.getInPin(1))
        self.and1.getOutPin(0).addConnection(self.latch.getInPin(0))
        self.and2.getOutPin(0).addConnection(self.latch.getInPin(1))

        self.setOutPin(0, self.latch.getOutPin(0))
        self.setOutPin(1, self.latch.getOutPin(1))


"""
(data)   In0-----FAN-----NOT----|i0             o0
                 |              ****************------OUT0 (Q)
(enable) In1-----O--------------* GatedSRLatch *
                 |            i2*              *
                 |              ****************------OUT1 (not Q)
                 |--------------|i1             o1

"""
class DLatch(Gate):
    """
    A DLatch removes the possibilty of an invalid input state in a GatedSRLatch.

    In0 is the "data" line.
    In1 is the "enable" line.

    Set the enable line to False, to maintain previous state.
    Set the data line to True to "set" the latch.
        This sets OUT0 to True and OUT1 to False.
    SEt the data line to False to "reset" the latch.
        This set OUT0 to False and OUT1 to True.
    """
    def __init__(self):
        super(DLatch, self).__init__(2, 2)
        self.fan = Fan(2)
        self.notGate = Not()
        self.gsrLatch = GatedSRLatch()
        self.setInPin(0, self.fan.getInPin(0))
        self.setInPin(1, self.gsrLatch.getInPin(2))
        self.fan.getOutPin(0).addConnection(self.notGate.getInPin(0))
        self.fan.getOutPin(1).addConnection(self.gsrLatch.getInPin(1))
        self.notGate.getOutPin(0).addConnection(self.gsrLatch.getInPin(0))

        self.setOutPin(0, self.gsrLatch.getOutPin(0))
        self.setOutPin(1, self.gsrLatch.getOutPin(1))

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
    print "--------ThreeWayAnd------"
    enumeratePins(ThreeWayAnd())
    print "--------FourWayAnd------"
    enumeratePins(FourWayAnd())
    # print "--------FourToOneMux----"
    # enumeratePins(FourToOneMux())
    print "--------HalfAdder-------"
    enumeratePins(HalfAdder())
    print "--------OneBitAdder-----"
    enumeratePins(OneBitAdder())
    # print "--------FourBitAdder----"
    # enumeratePins(FourBitAdder())
    print "--------SRLatch---------"
    sr = SRLatch()
    sr.setIn(0, True)
    sr.setIn(1, False)
    print "set:  ", sr # set
    sr.setIn(0, False)
    print "same: ", sr # stays the same
    sr.setIn(1, False)
    print "same: ", sr # stays them same
    sr.setIn(1, True)
    print "reset:", sr # reset
    sr.setIn(1, False)
    print "same: ", sr # stays the same
    sr.setIn(0, False)
    print "same: ", sr # stays them same
    sr.setIn(0, True)
    sr.setIn(1, True)
    print "rand: ", sr
    print "--------GatedSRLatch----"
    enumeratePins(GatedSRLatch())
    print "--------DLatch----------"
    dl = DLatch()
    print "init: ", dl
    dl.setIn(1, True)
    dl.setIn(0, True)
    print "set:  ", dl # set
    dl.setIn(1, False)
    print "same: ", dl # stays the same
    dl.setIn(1, False)
    print "same: ", dl # stays them same
    dl.setIn(1, True)
    dl.setIn(0, False)
    print "reset:", dl # reset
    dl.setIn(1, False)
    print "same: ", dl # stays the same
    dl.setIn(0, False)
    print "same: ", dl # stays them same
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
