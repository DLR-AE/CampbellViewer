Getting started
===============

Requirements
------------
To run ``campbellviewer`` you need `pybladed <https://github.com/DLR-AE/pyBladed>`_.
You can install it using the following command

.. code-block:: bash

    $ pip install git+https://github.com/DLR-AE/pyBladed.git

.. note::
    If you're using Python >= 3.9 you might have trouble installing `pythonnet <https://pypi.org/project/pythonnet/>`_.
    You can install it by downloading the wheel file `here <https://www.lfd.uci.edu/~gohlke/pythonlibs/#pythonnet>`_,
    as suggested in this `discussion <https://stackoverflow.com/questions/67418533/how-to-fix-error-during-pythonnet-installation>`_.

Installation
------------

The campbellviewer supports Python 3.x or newer.

You can install the package using

.. code-block:: bash

    $ pip install git+https://github.com/DLR-AE/CampbellViewer.git

.. note::
    If you want to install a certain branch add **@<branch_name>** to the end of
    the URL.

To start the ``campbellviewer`` just type

.. code-block:: bash

    $ campbellviewer


Developers can clone the git to a local directory and run the following command
to install the package in development mode.

.. code-block:: bash

    $ pip install -e .
