Overview
--------

This has various logic gate and logic circuit implementations in Python. The goal was to start out with a few basic gates (and, or, xor, not) and connect them to build more complicated components (multiplexers, adders, etc).

There are the basic gate classes `And`, `Or`, `Xor`, and `Not`. These are all two-way gates (two inputs) implemented using Python's built-in boolean operations:

    --------And gate-------
    And<In=[0, 0] Out=[0]>
    And<In=[0, 1] Out=[0]>
    And<In=[1, 0] Out=[0]>
    And<In=[1, 1] Out=[1]>
    --------Or gate--------
    Or<In=[0, 0] Out=[0]>
    Or<In=[0, 1] Out=[1]>
    Or<In=[1, 0] Out=[1]>
    Or<In=[1, 1] Out=[1]>
    --------Not gate-------
    Not<In=[0] Out=[1]>
    Not<In=[1] Out=[0]>
    --------Xor gate-------
    Xor<In=[0, 0] Out=[0]>
    Xor<In=[0, 1] Out=[1]>
    Xor<In=[1, 0] Out=[1]>
    Xor<In=[1, 1] Out=[0]>

We use these to create more complicated gates. For example, we can create a half-adder that adds two bits together:

    // A half adder
    // O indicates wires do not cross
    In0  In1
     |    |
     |    +----XOR---OUT1 (sum)
     |    |    |
     +----O----|
     |    |    
     |    |----| 
     |         |
     |---------AND---OUT0 (carry)

And then we can use the half-adder to create a one-bit adder. This adds two one-bit numbers and a carry bit:

    // A one-bit adder
    // i0, i1 are input pins to an internal gate
    // o0, o1 are output pins from an internal gate
    // O indicates wires do not cross
    In0----------+-------|      i1
                 |       XOR-----************* o1
    In1---+------O-------|       * HalfAdder *--------------OUT1 (sum)
          |      |               *           *
    In2---O------O---------------*************
          |      |              i0           | o0
          |      |                           |-------|
          |      |------------|                      OR-----OUT0 (carry)
          |                   AND--------------------|
          |-------------------|

We can then create a four-bit adder using four one-bit adders. This will add two-four bit numbers and a one-bit carry. It outputs the four-bit sum and a one-bit carry. The carry bit travels horizontally across the adder:

    // A four-bit adder
    // i0, i1 are input pins to an internal gate
    // o0, o1 are output pins from an internal gate
               In0   In1              In2   In3              In4   In5             In6   In7
                |     |                |     |                |     |               |     |
                |i0   |i1              |i0   |i1              |i0   |i1             |i0   |i1
            ****************       ****************       ****************      ****************
    In8-----* OneBitAdder1 *-------* OneBitAdder2 *-------* OneBitAdder3 *------* OneBitAdder4 *-----OUT4
          i2****************o0   i2****************o0   i2****************o0  i2****************o0
                    |o1                    |o1                    |o1                   |o1   
                    |                      |                      |                     |
                   OUT0                   OUT1                   OUT2                  OUT3

Some of the other gates implemented include a few latches for storing one-bit of information, a 2-to-1 and 4-to-1 multiplexer, a 1-to-4 demultiplexer, a 4-to-2 encoder, and 2-to-4 decoder.

### Implementation ###

There is an abstract `Gate` base class which has a list of input pins and a list of output pins. We can set the input pins to `True` or `False`, and the gate will compute the values for each output pin. The classes `Or`, `Not`, `Xor`, `And`, and `SRLatch` are implemented by "cheating" -- they are implemented using Python's boolean operations. All other gates/circuits are implemented by connecting other gates together. As long as a class acts like `Gate`, we can connect it to other `Gate`s.

One issue that complicates the code a bit when connecting gates together is the propagation of output values from one gate to the input values of other gates. I handle this by making each pin an object:

  * A `Gate` has a list of `InputPin`s. Each `InputPin` stores its assigned `Gate`. When the `InputPin`'s value changes, it tells the `Gate` to recompute/refresh its output values.
  * A `Gate` also has a list of `OutputPin`s. Each `OutputPin` can be connected to any number of other pins. When an `OutputPin` has its value updated, it copies its value to all of its connected pins.

So we connect `Gate`s by connecting an `OutputPin` from the one `Gate` to an `InputPin` of another:

    decoder.getOutPin(0).addConnection(andGate.getInPin(1))

Then value propagation works as follows:

  1. An `InputPin` has its value changed.
  2. The `InputPin` tells `g`, its assigned `Gate`, to refresh its output pins.
  3. An `OutputPin` of `g` has its value updated. It the sets the value of each of its connected pins, which are `InputPin`s associated with other `Gate`s. (then back to 1)

### Problems/Ideas ###

  * This doesn't handle loops in our circuits (we get infinite recursion). This is why `SRLatch` cannot be implemented in terms of other gates.
  * Going deeper would be interesting. We could implement the basic gates as electronic circuits composed of transistors and resistors.
  * There are still many more complicated parts, but it gets repetitive and tedious connecting each pin individually. It would be helpful to have some way of "lining up" all of the pins on two gates and connecting them all at once. Or maybe just some lighter syntax for connecting individual pins.
