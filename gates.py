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
			return self._inputs[index]
		raise GateException("No output pin %s on this gate." % index)

	def _setOut(self, index, value):
		""" Set an output pin """
		if 0 <= index < len(self._outputs):
			self._outputs[index] = value
		else:
			raise GateException("No output pin %s on this gate." % index)

	def _recomputeOutputs():
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

# # what is the point of this?
# class PinMapper(Gate):
# 	""" A pin mapper forwards pin values """

# 	def __init__(self, size):
# 		super(PinMapper, self).__init__(size, size)

# 	def _recomputeOutputs():
# 		for i in xrange(self.nInputs):
# 			self._setOut(i, self._inputs[i])

class PinConnector(object):
	"""
	This connects an output pin of one gate to the input pin of another gate.
	For example, to connect the output pins of 2 AND gates to the input pins of an OR gate:
		and1 = And()
		and2 = And()
		or = Or()
		p = PinConnector()
		p.connect(and1, 0, or, 0)  # connect and1 output pin 0 to or input pin 0
		p.connect(and2, 0, or, 1)  # connect and2 output pin 0 to or input pin 1
	Then you can route these connections:
		p.setInput(and1, 0, True)	# set input pin 0 of and1 to True
		p.setInput(and1, 1, True)	# set input pin 1 of and1 to True
	Now and1 output 0 has value True while and and2 output 1 has value False,
	so the OR gate is receiving True on input 0 and FAlse on input 1.
	You can access these in either of the following ways:
		p.getOutput(or, 0)	# returns True
		or.getOut(0)		# returns True

	WARNING: This doesn't handle recursive connections.
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

	def setInput(self, gate, pin, value):
		"""
		Set the given input pin on the given gate to the given value.
		Raises a GateException if the gate does not have an output pin
			connected to any other gate's input pin.
		"""
		if gate not in self._connections:
			raise GateException("Gate %s has no connections to any other gates in this PinConnector" % gate)
		gate.setIn(pin, bool(value))

		for (fromPin, toGate, toPin) in self._connections[gate]:
			toGate.setIn(toPin, gate.getOut(fromPin))

	def getOutput(self, gate, pin):
		return gate.getOut(pin)

	def __str__(self):
		result = "PinConnector[\n"
		for gate, entry in self._connections.iteritems():
			result += "  %s -> %s,\n" % (gate, entry)
		return result + "]"

	def __repr__(self):
		return str(self)

# Problems with this
#	1. How to compute the output pins?
#		If the user specifies some number of output pins,
#		how do we check this? If they ask for the value on
#		some output pin, how do I find it?
#	2. How do we cherry-pick pins when we connect gates together?
#		Can we connect output pin0 of andGate0 and output pin1 of andGate1
#		to the inputs of a single Or gate?
#
class Connector(Gate):
	""" 
	This connects gates together.
	For example, you could create a NAND by connecting an AND gate and a NOT gate:
		andGate = And()
		notGate = Not()
		nandGate = Connector()
		pins = c.addInputGate(andGate)	 # important to use the same andGate instance here
		c.connect(andGate, OrGate)		 # and here
	"""

	def __init__(self, nInputs, nOutputs):
		super(Connector, self).__init__(nInputs, nOutputs)
		self._gates = set()
		self._inputGates = []

	def addInputGate(self, gate):
		""" 
		The given gate is attached to the next free pin(s).
		Raises a GateException if not enough pins for the gate.
		Returns the indices of the pins that are reserved for the gate.
		"""

		if len(self._inputs) + gate.nInputs >= self.nInputs:
			raise GateException("Not enough pins to add this gate %s (%s/%s are filled) " 
				% (gate, len(self._inputs), self.nInputs))
		
		self._inputs += ([0] * gate.nInputs)
		self._gates.add(Node(gate))			 	# gives us all the gates
		self._inputGates.append(Node(gate))		# gives us the input gates

		return range(len(self._inputs) - gate.nInputs, len(self._inputs))

	def _findGateNode(self, gate):
		for x in self._gates:
			if x.payload == gate:
				return x
		raise None

	def connect(self, a, b):
		"""
		Connect the output pins of gate a (which must already exist in this connector) 
		to the input pins of gate b. A GateException is raised if a does not have the
		same number of output pins as b has input pins
		"""
		n = self._findGateNode(a)
		if n == None:
			raise GateException("No gate %s found to connect to %s" % (a, b))
		elif a.nOutputs != b.nInputs:
			raise GateException("Cannot connect gate %s (%s outputs) to %s (%s inputs)" 
				% (a, a.nOutputs, b, b.nInputs))
		n.addChild(Node(b))

	def _sendCurrent(self, gateNode):
		""" 
		Starting from gateNode, set the output pins from gateNode to the
		pins of its children.
		"""


	def _recomputeOutputs(self):
		pin = 0
		for gateNode in self._inputGates:
			gate = gateNode.payload
			for i in xrange(gate.nInputs):
				gate.setIn(i, self._inputs[pin])
				pin += 1
			endNode = self._sendCurrent(gateNode)




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
		for i, p in enumerate(pins):
			gate.setIn(i, p)
		print gate

if __name__ == '__main__':
	# print "--------And gate-------"
	# enumeratePins(And())
	# print "--------Or gate--------"
	# enumeratePins(Or())
	# print "--------Not gate-------"
	# enumeratePins(Not())
	# print "--------Xor gate-------"
	# enumeratePins(Xor())

	# nodes = map(lambda x: Node(x), range(4))
	# nodes[0].addChild(nodes[1])
	# nodes[0].addChild(nodes[2])
	# nodes[1].addChild(nodes[2])
	# nodes[1].addChild(nodes[3])
	# nodes[2].addChild(nodes[1])
	# nodes[2].addChild(nodes[3])
	# Node.printGraph(nodes[0])

	and1 = And()
	and2 = And()
	orGate = Or()
	p = PinConnector()
	print p
	p.connect(and1, 0, orGate, 0)
	p.connect(and2, 0, orGate, 1)
	print p
	print orGate
	p.setInput(and1, 0, True)
	p.setInput(and1, 1, True)
	print and1
	print p
	print 
