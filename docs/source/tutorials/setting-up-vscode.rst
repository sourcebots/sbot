Setting up Visual Studio Code
=============================

This tutorial will guide you through setting up the `VS Code <https://code.visualstudio.com/>`__ editor
with support for our robot software.

1. Search for and open up Python 3.7 from the start menu.
2. Enter the following lines of code:

.. code:: python

    import sys
    import subprocess
    subprocess.call([sys.executable, "-m", "pip", "install", "sbot", "--user"])

3. Search for and open up Visual Studio Code from the start menu.
4. Open a new folder where you'd like to store your robot code.
5. Save it