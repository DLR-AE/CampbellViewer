.. _sec_dev_getting_started:

Getting started
===============

Installation
------------

Developers can clone the git to a local directory and run the following command
to install the package in development mode.

.. code-block:: console

    pip install -e .

Make sure you also have the dependencies for development installed.

.. code-block:: console

    pip install -r requirements-dev.txt


Building the documentation
---------------------------

If you want to build the documentation locally, navigate to the `.\docs` folder
and type

.. code-block:: console

    make html
