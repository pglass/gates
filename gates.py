class GateException(Exception):
	def __init__(self, msg):
		super(GateException, self).__init__(msg)

class Gate(object):
	""" 
	This defines a base class for logic gates.
	A Gate has a number of input pins and a number of output pins, indexed from 0.
	Inputs and outputs are either True or False.

	Subclasses need to override the _recomputeOutputs(),
	Subclasses should not need to override the setIn() or getOut() methods.
	"""

	def __init__(self, nInputs = 0, nOutputs = 0):
		self.nInputs = nInputs
		self.nOutputs = nOutputs
		self._inputs = [False] * nInputs
		self._outputs = [False] * nOutputs

	def setIn(self, index, value):
		""" Set the given input to bool(value) """
		if 0 <= index < len(self._inputs):
			self._inputs[index] = bool(value)
			self._recomputeOutputs()
		else:
			raise GateException("No input pin %s on this gate." % index)

	def getOut(self, index):
		""" Get the current value of an output pin """
		if 0 <= index < len(self._inputs):
			return self._outputs[index]
		raise GateException("No output pin %s on this gate." % index)

	def _setOut(self, index, value):
		""" Set an output pin """
		if 0 <= index < len(self._outputs):
			self._outputs[index] = value
		else:
			raise GateException("No output pin %s on this gate." % index)

	def _recomputeOutputs(self):
		""" Reimplement in subclass """
		raise NotImplementedError("Don't instantiate this base class")

	def __str__(self):
		def TFto10(x):
			""" Convert True to 1 and False to 0 """
			if x:
				return 1
			return 0

		return "%s<In=%s Out=%s>" % (self.__class__.__name__, 
									 map(TFto10, self._inputs), 
									 map(TFto10, self._outputs))

	def __repr__(self):
		return str(self)

class And(Gate):
	def __init__(self):
		super(And, self).__init__(2, 1)

	def _recomputeOutputs(self):
		self._setOut(0, all(self._inputs))

class Or(Gate):
	def __init__(self):
		super(Or, self).__init__(2, 1)

	def _recomputeOutputs(self):
		self._setOut(0, any(self._inputs))

class Not(Gate):
	def __init__(self):
		super(Not, self).__init__(1, 1)

	def _recomputeOutputs(self):
		self._setOut(0, not self._inputs[0])

class Xor(Gate):
	def __init__(self):
		super(Xor, self).__init__(2, 1)

	def _recomputeOutputs(self):
		self._setOut(0, self._inputs[0] ^ self._inputs[1])


class Node(object):
	def __init__(self, payload = None):
		self.children = []		# the children are ordered by insertion time
		self.payload = payload

	def addChild(self, value):
		if type(value) != Node:
			value = Node(value)
		if value not in self.children:
			self.children.append(value)

	def __cmp__(self, other):
		return cmp(self.payload, other.payload)

	def __hash__(self):
		return hash(str(self))

	@staticmethod
	def printGraph(node):
		frontier = [node]
		seenNodes = set()
		while len(frontier) > 0:
			n = frontier.pop()
			seenNodes.add(n)
			print "%s -> %s" % (n.payload, map(lambda x: x.payload, n.children))
			frontier += filter(lambda x: not (x in seenNodes or x in frontier), n.children)

	def __str__(self):
		return "Node[%s]" % self.payload

	def __repr__(self):
		return str(self)

class PinConnector(object):
	"""
	This is a class to manage connections between pins of different gates.
	You should generally only need one instance of this class for a set of gates.
	For example:
		and1 = And()
		and2 = And()
		orGate = Or()
		p = PinConnector()
		p.connect(and1, 0, orGate, 0)	# connect output 0 of and1 to input 0 of orGate
		p.connect(and2, 0, orGate, 1)   # connect output 0 of and2 to input 0 of orGate
	This works by altering the setIn method of each `and1` and `and2` to additionally
	copy the new output value to the apprioriate pin on the orGate. That means you
	can do the following:
		and1.setIn(0, True)
		and1.setIn(1, True)
	And you will see:
		print orGate.getOut(0) 	# True


	WARNING: This does not handle recursive connections
	"""
	def __init__(self):
		self._connections = {}

	def connect(self, fromGate, fromPin, toGate, toPin):
		""" Connect ouput pin `fromPin` on gate `fromGate` to the input pin `toPin` on gate `toGate` """
		entry = (fromPin, toGate, toPin)
		if fromGate in self._connections:
			self._connections[fromGate].append(entry)
		else:
			self._connections[fromGate] = [entry]

		# alter fromGate.setIn to update the pins it's connected to
		setIn = fromGate.setIn
		def f(p, v):
			setIn(p, bool(v))
			for (fromPin, toGate, toPin) in self._connections[fromGate]:
				toGate.setIn(toPin, fromGate.getOut(fromPin))
		fromGate.setIn = f

	def __str__(self):
		result = "PinConnector["
		for gate, entry in self._connections.iteritems():
			result += "\n  %s -> %s," % (gate, entry)
		if result.endswith(','):
			result = result[:-1] + "\n"
		return result + "]"

	def __repr__(self):
		return str(self)


class Nand(Gate):
	""" A NAND gate created with an AND and a NOT gate """
	def __init__(self):
		super(Nand, self).__init__(2, 1)
		self.andGate = And()
		self.notGate = Not()
		self.pc = PinConnector()
		self.pc.connect(self.andGate, 0, self.notGate, 0)
		self._inputs = self.andGate._inputs
		self._outputs = self.notGate._outputs

		self.setIn(0, False)
		self.setIn(0, False)

	def setIn(self, pin, value):
		self.andGate.setIn(pin, value)

class Nor(Gate):
	""" A NOR gate created with and OR and a NOT """
	def __init__(self):
		super(Nor, self).__init__(2, 1)
		self.orGate = Or()
		self.notGate = Not()
		self.pc = PinConnector()
		self.pc.connect(self.orGate, 0, self.notGate, 0)
		self._inputs = self.orGate._inputs
		self._outputs = self.notGate._outputs

		self.setIn(0, False)
		self.setIn(0, False)

	def setIn(self, pin, value):
		self.orGate.setIn(pin, value)

class Xnor(Gate):
	""" An XNOR gate create with an XOR and a NOT """
	def __init__(self):
		super(Xnor, self).__init__(2, 1)
		self.xorGate = Xor()
		self.notGate = Not()
		self.pc = PinConnector()
		self.pc.connect(self.xorGate, 0, self.notGate, 0)
		self._inputs = self.xorGate._inputs
		self._outputs = self.notGate._outputs

		self.setIn(0, False)
		self.setIn(0, False)

	def setIn(self, pin, value):
		self.xorGate.setIn(pin, value)

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

if __name__ == '__main__':
	print "--------And gate-------"
	enumeratePins(And())
	print "--------Or gate--------"
	enumeratePins(Or())
	print "--------Not gate-------"
	enumeratePins(Not())
	print "--------Xor gate-------"
	enumeratePins(Xor())
	print "--------Nand gate------"
	enumeratePins(Nand())
	print "--------Nor gate------"
	enumeratePins(Nor())
	print "--------Xnor gate------"
	enumeratePins(Xnor())

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
