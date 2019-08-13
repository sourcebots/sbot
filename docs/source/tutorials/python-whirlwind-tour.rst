Python: A Whirlwind Tour
========================

In this tutorial, we'll introduce the basic concepts of programming,
which will be central to the programs that you will run on your robot.
There are many different languages in which computers can be programmed,
all with their advantages and disadvantages, but we use
`Python <https://www.python.org/>`__, specifically 3.6. We chose Python because it's easy to learn,
but also elegant and powerful.

At the end of the tutorial are exercises. The first ones for each
section should be quite easy, while the higher-numbered exercises will
be harder. Some will be very hard; try these if you're up for a
challenge.

Before we begin, a word on learning. The way that you learn to code is
by doing it; make sure you try out the examples, fiddle with them, break
them, try some of the exercises.

Using an interpreter
--------------------

To run Python programs you need a something called an interpreter. This
is a computer program which interprets human-readable Python code into
something that the computer can execute. There are a number of online
interpreters that should work even on a locked-down computer, such as
you will probably find in your college.

If your computer has a compatible browser, go to http://repl.it and
select *Python3* from the dropdown. Enter your program in the box on the
left, and click the arrow to run it.

If your browser isn't compatible, another good online interpreter can be
found at http://codeskulptor.org. It's very similar; simply enter your
program into the left pane and click the play button to run it. The
output will appear in the right pane.

Whichever you choose, test it with this classic one line program:

.. code:: python

    print("Hello World!")

The text ``Hello World!`` should appear in the output box.

There's nothing particularly wrong with online interpreters for our
needs, but if you want to use Python for something more advanced you'll
want an interpreter which runs directly on your computer. Downloads are
available for all common OS's from `the
website <https://www.python.org/downloads/>`__.

Statements
----------

A statement is a line of code that does something. A program is a list
of statements. For example:

.. code:: python

    x = 5
    y = (x * 2) + 4
    print("Number of bees:", y - 2)

The statements are executed one by one, in order. This example would
give the output ``Number of bees: 12``.

As you may have guessed, the ``print`` statement displays text on the
screen, while the other two lines are simple algebra.

Strings
~~~~~~~

When you want the interpreter to treat something as a text value (for
example, after the ``print`` statement above), you have to surround it
in quotes. You can use either single (``'``) or double (``"``) quotes,
but try to be consistent. Pieces of text that are treated like this are
called 'strings'.

Comments
~~~~~~~~

Placing a hash (``#``) in your program ignores anything after the hash.

For example:

.. code:: python

    # This is a comment
    print("This isn't.")  # But this is!

You should use comments whenever you think that it is not completely
clear what a statement or block of statements does, especially as you
are working in teams! Also bear in mind the varying coding skills of
your team. You might be the best coder in your team, but what if you
were taken ill the day before the competition, and your team-mates had
to fix your code?

Comments are also useful for temporarily removing statements from your
code, for testing:

.. code:: python

    x = 42
    #x = x - 4
    print("The answer is", x)

This example would output ``The answer is 42``, as the subtraction is
not executed.

Variables
---------

Variables store values for later use, as in the first example. They can
store many different things, but the most relevant here are numbers,
strings (blocks of text), booleans (``True`` or ``False``) and lists
(which we'll come to later).

To set a variable, simply give its name, followed by ``=`` and a value.
For example:

.. code:: python

    x = 8
    my_string = "Tall ship"

You can ask the user to put some text into a variable with the ``input``
function (we'll cover functions in more detail later):

.. code:: python

    name = input("What is your name?")

Identifiers
~~~~~~~~~~~

Certain things in your program, for example variables and functions,
will need names. These names are called 'identifiers' and must follow
these rules:

-  Identifiers can contain letters, digits, and underscores. They may
   not contain spaces or other symbols.
-  An identifier cannot begin with a digit.
-  Identifiers are case sensitive. This means that ``bees``, ``Bees``
   and ``BEES`` are three different identifiers.

Code blocks and indentation
---------------------------

Python is reasonably unique in that it cares about indentation, and uses
it to decide which statements are referred to by things like ``if``
statements.

In most other programming languages, if you don't indent your code it
will run just fine, but any poor soul who has to read your code will
hunt you down and hit you around the head with a large, wet fish. In
Python, you'll just get an error, which we're sure you'll agree is
preferable.

A group of consecutive statements that are all indented by the same
distance is called a block. ``if`` statements, as well as functions and
loops, all refer to the block that follows them, which must be indented
further than that statement. An example is in order. Let's expand the
first ``if`` example:

.. code:: python

    name = input("What is your name?")
    email = "Bank of Nigeria: Tax Refund"
    if name == "Tim":
        print("Hello Tim.")
        if email != "":
            print("You've got an email.")

            # (blocks can contain blank lines in the middle)
            if email != "Bank of Nigeria: Tax Refund":
                print("Looks legitimate, too!")
        else:
            print("No mail.")

    else:
        print("You're not Tim!")

    print("Python rocks.")

Output (for "Tim" as before):

.. code:: text

    Hello Tim.
    You've got an email!
    Python rocks.

To find the limits of an ``if`` statement, just scan straight down until
you encounter another statement on the same indent level. Play around
with this example until you understand what's happening.

One final thing: Python doesn't mind *how* you indent lines, just so
long as you're consistent. Some text editors insert indent characters
when you press tab; others insert spaces (normally four). They'll often
look the same, but cause errors if they're mixed. If you're using an
online interpreter, you probably don't need to worry. Otherwise, check
your editor's settings to make sure they're consistent. Four spaces per
indent level is the convention in Python. We'll now move on from this
topic before that last sentence causes a `flame
war <https://www.youtube.com/watch?v=SsoOG6ZeyUI>`__.

Lists
-----

Lists store more than one value in a single variable and allow you to
set and retrieve values by their position ('index') in the list. For
example:

.. code:: python

    shopping_list = ["Bread", "Milk", "PNP Transistors", "Newspaper"]
    print(shopping_list[0])
    shopping_list[3] = "Magazine"
    print(shopping_list[2])
    print(shopping_list[3])

Output:

.. code:: text

    Bread
    PNP Transistors
    Magazine

.. Warning::
    Like most other programming languages, indices
    start at 0, not 1. Due to this, the last element of this four-element
    list is at index 3. Attempting to retrieve ``shopping_list[4]`` would
    cause an error.

You can find out the length of a list with the ``len`` function, like
so:

.. code:: python

    shopping_list = ["Bread", "Milk", "PNP Transistors", "Newspaper"]
    print("There are", len(shopping_list), "items on your list.")

Finally, you can add a value to the end of a list with the ``append``
method:

.. code:: python

    shopping_list = ["Bread", "Milk", "PNP Transistors", "Newspaper"]
    shopping_list.append("Mince pies in October")
    print(shopping_list)

The values in a list can be of any type, even other lists. Also, a list
can contain values of different types.

There are various other useful data structures that are beyond the scope
of this tutorial, such as dictionaries (which allow indices other than
numbers). You can find out more about these in `python's
documentation <http://docs.python.org/tutorial/datastructures.html>`__.

``while`` loops
---------------

The ``while`` loop is the most basic type of loop. It repeats the
statements in the loop while a condition is true. For example:

.. code:: python

    x = 10
    while x > 0:
        print(x)
        if x == 5:
            print("Half way there!")

        x = x - 1

    print("Zero!")

Output:

.. code:: text

    10
    9
    8
    7
    6
    5
    Half way there!
    4
    3
    2
    1
    Zero!

The condition is the same as it would be in an ``if`` statement and the
block of code to put in the loop is denoted in the same way, too.

``for`` loops
-------------

The most common application of loops is in conjunction with lists. The
``for`` loop is designed specifically for that purpose. For example:

.. code:: python

    shopping_list = ["Bread", "Milk", "PNP Transistors", "Newspaper"]
    for x in shopping_list:
        print("[ ]", x)

The code is executed once for each item in the list, with ``x`` set to
each item in turn. So, the output of this example is:

.. code:: text

    [ ] Bread
    [ ] Milk
    [ ] PNP Transistors
    [ ] Newspaper

Unfortunately, this method doesn't tell you the index of the current
item. ``x`` is only a temporary variable, so modifying it has no effect
on the list itself (try it). This is where the ``enumerate`` function
comes in (see `Calling functions <#calling-functions>`__). It tells us
the index of each value we loop over. An example with numbers:

.. code:: python

    prices = [4, 5, 2, 1.50]
    # Add VAT
    for index, value in enumerate(prices):
        prices[index] = value * 1.20

    print(prices)

Output:

.. code:: text

    [4.8, 6.0, 2.4, 1.7999999999999998]

Calling functions
-----------------

Functions are pre-written bits of code that can be run ('called') at any
point. The simplest functions take no parameters and return nothing. For
example, the ``exit`` function ends your program prematurely:

.. code:: python

    x = 10
    while x > 0:
        print(x)
        x = x - 1
        if x == 5:
            exit()  # not supported in repl.it!

This will output the numbers 10 to 6, and then stop. Not very useful.
However, most functions take input values ('parameters') and output
something useful (a 'return value'). For example, the ``len`` function
returns the length of the given list:

.. code:: python

    my_list = [42, "BOOMERANG!!!", [0, 3]]
    print(len(my_list))

Output:

.. code:: text

    3

Combined with the ``range`` function, which returns a list of numbers in
a certain range, you get a list of indices for the list (you might want
to look back at that second ``for`` example).

.. code:: python

    my_list = [42, "BOOMERANG!!!", [0, 3]]
    print(range(len(my_list)))

Output:

.. code:: text

    [0, 1, 2]

The ``range`` function can also take multiple parameters:

.. code:: python

    print(range(5))           # numbers from 0 to 4.
    print(range(2, 5))         # numbers from 2 to 4.
    print(range(1, 10, 2))     # odd numbers from 1 to 10

Output:

.. code:: text

    [0, 1, 2, 3, 4]
    [2, 3, 4]
    [1, 3, 5, 7, 9]

There are many built-in functions supplied with Python (see
`appendix <#built-in-functions>`__). Most are in 'modules', collections
of functions which have to be imported. For example, the ``math`` module
contains mathematical functions. To use the ``sin`` function, we must
import it:

.. code:: python

    import math

    print(math.sin(math.pi / 2))

Defining functions
~~~~~~~~~~~~~~~~~~

Of course, you'll want to make your own functions. To do this, you
precede a block of code with a ``def`` statement, specifying an
identifier for the function, and any parameters you might want. For
example:

.. code:: python

    def annoy(num_times):
        for i in range(num_times):
            print("Na na na-na na!")

    annoy(3)

The output would be three annoying lines of ``Na na na-na na!``.

To return a value, use the ``return`` statement. A rather trivial
example:

.. code:: python

    def multiply(x, y):
        return x * y

    print(multiply(2, 3))

Using functions effectively
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without functions, most programs would be very hard to read and
maintain. Here's an example (admittedly a little contrived):

.. code:: python

    my_string = "All bees like cheese when they're wearing hats."
    x = 0
    for c in my_string:
        if c == "a":
            x = x + 1

    y = 0
    for c in my_string:
        if c == "e":
            y = y + 1

Before we explain the example, try and figure out what it does. What do
``x`` and ``y`` represent?

Now, let's refine it with functions:

.. code:: python

    def count_letter(string, l):
        x = 0
        for c in string:
            if c == l:
                x = x + 1

        return x

    my_string = "Bees like cheese when they're wearing hats."

    x = count_letter(my_string, "a")
    y = count_letter(my_string, "e")

This version has a number of advantages:

-  It's far more obvious what the program does.
-  The program is shorter, and cleaner.
-  The code for counting letters in a string is in only one place, and
   can be reused.

The last point has another advantage. There's a bug in this program:
upper-case letters aren't counted. It's easy to fix, but in the function
version we only have to apply the fix in one place. True, it would only
be two places in the original, but in a major program, it could be
thousands.

You should try and use functions wherever you see multiple lines of code
that are repeated, or find yourself writing code to do the same thing
(or a similar thing) more than once. In these situations, look at the
relevant bits of code and try to think of a way to put it into a
function.

Scope
-----

When you set a variable inside a function, it will only keep its value
inside that function. For example:

.. code:: python

    x = 2

    def foo():
        x = 3
        print("In foo(), x =", x)

    foo()
    print("Outside foo(), x =", x)

Output:

.. code:: text

    In foo(), x = 3
    Outside foo(), x = 2

This can get quite confusing, so it's best to avoid giving variables
inside functions ('local' variables) the same identifier as those
outside. If you want to get information out of a function, ``return``
it.

This concept is called 'scope'. We say that variables which are changed
inside a function are in a different scope from those outside.

You can have functions within functions, and this can actually be quite
useful. In this situation, each nested function will also have its own
scope.

Exercises: variables and mathematics
------------------------------------

Average calculator
~~~~~~~~~~~~~~~~~~

The first two lines of this program put two numbers entered by the user
into variables ``a`` and ``b``. (The ``input`` function is like
``input``, but returns a number (e.g. ``42``) when you enter one, rather
than a string (like ``"42"``).) Replace the comment with code that
averages the numbers and puts them in a variable called ``average``.

.. code:: python

    a = input("Enter first number: ")
    b = input("Enter second number: ")

    # Store the average of a and b in the variable `average`

    print("The average of", a, "and", b, "is", average)

Run your code and check that it works.

Distance calculator
~~~~~~~~~~~~~~~~~~~

Write a program which uses ``input`` to take an X and a Y coordinate,
and calculate the distance from (0, 0) to (X, Y) using Pythagoras'
Theorem. Put the code into an interpreter and run it. Does it do what
you expected?

.. Tip::
    You can find the square root of a number by raising
    it to the power of 0.5, for example, ``my_number ** 0.5``.

**Extension:** can you adapt the program to calculate the distance
between any two points?

Booleans and ``if`` statements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A boolean value is either ``True`` or ``False``. For example:

.. code:: python

    print(42 > 5)
    print(4 == 2)

Output:

.. code:: text

    True
    False

``<`` and ``==`` are operators, just like ``+`` or ``*``, which return
booleans. Others include ``<=`` (less than or equal to), ``>``, ``>=``
and ``!=`` (not equal to). You can also use ``and``, ``or``, and ``not``
(see the `Operators <#operators>`__ appendix).

``if`` statements execute code only if their condition is true. The code
to include in the ``if`` is denoted by a number of indented lines. To
indent a line, press the tab key or insert four spaces at the start. You
can also include an ``else`` statement, which is executed if the
condition is false. For example:

.. code:: python

    name = input("What is your name?")
    if name == "Tim":
        print("Hello Tim.")
        print("You've got an email.")
    else:
        print("You're not Tim!")

    print("Python rocks!")

If you typed "Tim" at the prompt, this example would output:

.. code:: text

    Hello Tim.
    You've got an email.
    Python rocks!

Having another ``if`` in the ``else`` block is very common:

.. code:: python

    price = 50000 * 1.3
    if price < 60000:
        print("We can afford the tall ship!")
    else:
        if price < 70000:
            print("We might be able to afford the tall ship...")
        else:
            print("We can't afford the tall ship. :-(")

So common that there's a special keyword, ``elif``, for the purpose. So,
the following piece of code is equivalent to the last:

.. code:: python

    price = 50000 * 1.3
    if price < 60000:
        print("We can afford the tall ship!")
    elif price < 70000:
        print("We might be able to afford the tall ship...")
    else:
        print("We can't afford the tall ship. :-(")

Both output:

.. code:: text

    We might be able to afford the tall ship...

Exercises: ``if`` statements and blocks
---------------------------------------

So many ``if``\ s
~~~~~~~~~~~~~~~~~

Without running it, work out what output the following code will give:

.. code:: python

    some_text = "Duct Tape"
    if 5 > 4:
        print("Maths works.")
        if some_text == "duct tape":
            print("The case is wrong.")
        elif some_text == "Duct Tape":
            print("That's right.")
        else:
            print("Completely wrong.")
    else:
        print("Oh-oh.")

Run the code and check your prediction.

Age detection tool
~~~~~~~~~~~~~~~~~~

Write a program that asks the user for their age, and prints a different
message depending on whether they are under 18, over 65, or in between.

Exercises: lists and loops
--------------------------

A better average calculator
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write a program which calculates the average of a list of numbers. You
can specify the list in the code.

**Extension:** You can tell when a user has not entered anything at a
``input`` prompt when it returns the empty string, ``""``. Otherwise, it
returns a string (like "42.5"), which you can turn into a number with
the ``float`` function. Additionally, extend your program to let the
user enter the list of values. Stop asking for new list entries when
they do not enter anything at the ``input`` prompt. Example of how to
recognize when a user doesn't enter anything:

.. code:: python

    var = input("Enter a number: ")
    if var == "":
        print("You didn't enter anything!")
    else:
        print("You entered", float(var))

Fizz buzz
~~~~~~~~~

Write a program which prints a list of numbers from 0 to 100, but
replace numbers divisible by 3 with "Fizz", numbers divisible by 5 with
"Buzz", and numbers divisible by both with "Fizz Buzz".

**Extension:** create a list of numbers, and replace a number with
"Fuzz" if it is a multiple of any number in the list.

Trees and triangles
~~~~~~~~~~~~~~~~~~~

You can combine (or 'concatenate') strings in Python with the ``+``
operator:

.. code:: python

    str = "Hello "
    str = str + "World!"
    print(str)

Write a program that asks the user for a number, and then prints a
triangle of that height, with its right angle at the bottom left. For
example, given the number 3, the program should output:

.. code:: text

    *
    **
    ***

Try the same, but with the right angle in the top-right, like so (again,
for input 3):

.. code:: text

    ***
     **
      *

**Extension:** print out a tree shape of the given size. For example, a
tree of size 4 would look like this:

.. code:: text

       *
      ***
     *****
    *******
       *
       *

Exercises: functions
--------------------

Trigonometry
~~~~~~~~~~~~

Write a program that takes as input an angle (in radians) and the length
of one side (of your choice) of a right-angled triangle. Print out the
length of all sides of the triangle.

You'll need the functions contained in the ``math``
module `(docs here) <http://docs.python.org/library/math.html>`_

.. NOTE::
    Python uses radians for its angles. If you are not comfortable with
    radians, you can use the ``radians`` function in the ``math`` module to
    convert to radians from degrees.

**Extension:** you can return multiple values from a function like so:

.. code:: python

    def foo():
        return 1, 2, 3

    x, y, z = foo()

Wrap your triangle calculation code in a function.

Greeting
~~~~~~~~

Write a function that takes a name as an input, and prints a message
greeting that person.

Average function
~~~~~~~~~~~~~~~~

Wrap the code for your average calculator from the Lists and Loops
exercises in a function that takes a list as a parameter and returns its
average.

What to do next
---------------

As mentioned at the start, there are loads of Python exercises out there
on the Web. If you want to learn some more advanced concepts, there are
more tutorials out there too. `Here's </tutorials/intro-to-python/>`__
our recommendations of tutorials from
`Codecademy <https://www.codecademy.com/>`__.

Appendices
----------

Operators
~~~~~~~~~

There are three types of operators in Python: arithmetic, comparison,
and logical. I'll list the most important.

Arithmetic
^^^^^^^^^^

The usual mathematical order (BODMAS) applies to these, just like in
normal algebra.

``+``, ``-``, ``*``, ``/``
    Self-explanatory.
``%``
    Remainder. For example, ``5 % 2`` is 1, ``4 % 2`` is 0.
``**``
    power (e.g. ``4 ** 2`` is 4 squared)

Comparison
^^^^^^^^^^

These return a boolean (``True`` or ``False``) value, and are used in
``if`` statements and ``while`` loops. These are always done after
arithmetic.

``==``, ``!=``
    equal to, not equal to
``<``, ``<=``, ``>``, ``>=``
    less than, less than or equal to, greater than, etc.
``in``
    returns true if the item on the left is contained in the item on the
    right. The items can be strings, lists, or other objects. For
    example:

.. code:: python

    if "car" in "Scarzy's hair":
        print("Of course.")

.. code:: python

    if 7 in [2, 35, 7, 8]:
        print("Found a seven!")

Logical
^^^^^^^

These operators are ``and``, ``or``, and ``not``. They are done after
both arithmetic and comparisons. They're pretty self-explanatory, with
an example:

.. code:: python

    x = 5
    y = 8
    z = 2

    if x == 5 and y == 3:
        print("Yes")
    else:
        print("No")

    print(x == 5 or not y == 8)         # could use y != 8 instead
    print(x == 2 and y == 3 or z == 2)  # needs brackets for clarity!

Output:

.. code:: text

    No
    True
    True

When more than one boolean operator is used in an expression, ``not`` is
performed first (as it works on a single operand). After this, ``and``
is done before ``or``, but you should use brackets instead of relying on
that fact, for readability. So, the last line of the example should
read:

.. code:: python

    print((x == 2 and y == 3) or z == 2)

Built-in functions
~~~~~~~~~~~~~~~~~~

A lot of functions are defined for you by Python. Those listed in `the
docs <http://docs.python.org/library/functions.html>`__ are always
available, and are the most commonly used, including ``len``, ``range``,
and enumerate.

Others are contained in modules. To use a function from a module, you
must ``import`` that module, like so:

.. code:: python

    import math
    print(math.sqrt(4))

One of the most useful modules for the moment will be the ``math`` module,
see `the python docs <http://docs.python.org/library/math.html>`__ for
more info.
