Setting up the PyCharm IDE
==========================

This tutorial will guide you through setting up the `PyCharm <https://www.jetbrains.com/pycharm/>`__ editor with support for our robot software. This means that the editor can do a better job of checking your code and suggesting as you type, saving you wasting time transferring your code to your robot only to find that a variable name has been mispelt, or something equally menial!

First, open up PyCharm from the Start Menu:

.. figure:: /_static/tutorials/setting-up-pycharm/001-start-menu.png
   :alt: Searching for and selecting PyCharm in the Start Menu.
   :scale: 75%

   Searching for and selecting PyCharm in the Start Menu.

It may ask you to read and accept their terms and conditions before you can proceed:

.. figure:: /_static/tutorials/setting-up-pycharm/002-privacy-policy.png
   :alt: The terms and conditions dialogue box.
   :scale: 75%

   The terms and conditions dialogue box.

Firstly, we will need to create a new project.

.. figure:: /_static/tutorials/setting-up-pycharm/003-create-project.png
   :alt: The welcome dialogue, with the Create New Project button.
   :scale: 75%

   The welcome dialogue, with the Create New Project button.

Next, you will need to configure the environment for your project. This ensures that
we are using a compatible version of Python (3.6 or later), and that Pycharm is aware of the 
other code running on, and controlling your robot.

At the top of the dialogue box, choose an appropriate location to save your code.

.. hint:: If you are using a university computer, files that are placed in your ``H:/`` drive will
   be synchronised and backed up across any other university computer.
   
Select *New Environment using Virtualenv*, and Python 3.6 for the base interpreter.

.. warning:: The location of Python 3.6 may vary by computer. Ask a volunteer for help if you are stuck.

.. figure:: /_static/tutorials/setting-up-pycharm/004-create-project-config.png
   :alt: Project configuration dialogue
   :scale: 75%

   Project configuration dialogue
   
Once PyCharm has finished loading, we need to create a new ``main.py``.

Right-click on your project name, select New -> Python File.

.. figure:: /_static/tutorials/setting-up-pycharm/005-new-file.png
   :alt: Create a new Python file
   :scale: 75%

   Create a new Python file
   
You will need to name your file ``main.py`` or your robot will not recognise it.

.. figure:: /_static/tutorials/setting-up-pycharm/006-new-file-config.png
   :alt: Naming your file
   :scale: 75%

   Naming your file

In order to get suggestions as you type your code, you'll need to install the same Python package that is used on your robot, which is called ``sbot``. You can do this by opening PyCharm's settings, navigating to the "Project Interpreter" tab, and pressing the Install button:

.. figure:: /_static/tutorials/setting-up-pycharm/007-settings.png
   :alt: Opening PyCharm's settings from the File menu.
   :scale: 75%

   Opening PyCharm's settings from the File menu.

.. figure:: /_static/tutorials/setting-up-pycharm/008-settings-tab.png
   :alt: The Project Interpreter tab in PyCharm's settings.
   :scale: 75%

   The Project Interpreter tab in PyCharm's settings.

.. figure:: /_static/tutorials/setting-up-pycharm/009-settings-install.png
   :alt: This button opens the package installation window.
   :scale: 75%

   This button opens the package installation window.

Enter "sbot" into the search bar and ensure it is selected in the pane on the left, then press "Install Package". This will take some time, so wait for the green success message.

.. figure:: /_static/tutorials/setting-up-pycharm/010-install-sbot.png
   :alt: Installing sbot
   :scale: 75%

   Installing sbot

.. figure:: /_static/tutorials/setting-up-pycharm/011-install-success.png
   :alt: Installation success
   :scale: 75%

   Installation success
   
You are now ready to program your robot. Pycharm will give you auto-suggestions and let you know if your
code is mis-spelt or has other common errors.

.. figure:: /_static/tutorials/setting-up-pycharm/012-code.png
   :alt: Code auto-suggestions
   :scale: 75%

   Code auto-suggestions
