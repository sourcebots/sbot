Advanced API
============

This page documents parts of the API that are for more advanced use. Most students will never need to use features from this page.

.. warning:: These features are for advanced users only.

Debug Mode
----------

It is possible to run your robot in "Debug Mode".

In "Debug Mode", your robot will print more information about what it is doing.

.. code:: python

   from sbot import Robot
   r = Robot(debug=True)

.. warning:: Debug mode is quite verbose. It will print a lot of information that you will not need.

Console Mode
------------

It is possible to test your code in "console mode".

This allows you to see every interaction that your robot makes with its hardware interactively. It may be useful to help debug your code.

Prerequisites
~~~~~~~~~~~~~

You need to have the ``sbot`` library available on your computer.

This can be achieved by following the `PyCharm Tutorial <tutorials/setting-up-pycharm>`__ or by installing ``sbot`` from PyPI_.

.. _PyPI: https://pypi.org/project/sbot/

Using Console Mode
~~~~~~~~~~~~~~~~~~

Console mode is activated by instantiating your ``Robot`` object with a ``ConsoleEnvironment``.

.. code:: python

   from sbot import Robot
   from sbot.env import ConsoleEnvironment
   r = Robot(environment=ConsoleEnvironment)

Robot code that is using Console Mode should be executed on a computer only.

* Run ``python3 main.py`` in a terminal window.
* Execute the code using PyCharm.

.. DANGER:: Running Console Mode code on a robot will result in a non-functioning robot.

Console Mode will print the current actions of your robot, and prompt you for information about it.
