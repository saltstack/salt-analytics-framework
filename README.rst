.. image:: https://img.shields.io/github/workflow/status/saltstack/salt-analytics-framework/CI?style=plastic
   :target: https://github.com/saltstack/salt-analytics-framework/actions/workflows/testing.yml
   :alt: CI


.. image:: https://readthedocs.org/projects/salt-analytics-framework/badge/?style=plastic
   :target: https://salt-analytics-framework.readthedocs.io
   :alt: Docs


.. image:: https://img.shields.io/codecov/c/github/saltstack/salt-analytics-framework?style=plastic&token=CqV7t0yKTb
   :target: https://codecov.io/gh/saltstack/salt-analytics-framework
   :alt: Codecov


.. image:: https://img.shields.io/pypi/pyversions/salt-analytics-framework?style=plastic
   :target: https://pypi.org/project/salt-analytics-framework
   :alt: Python Versions


.. image:: https://img.shields.io/pypi/wheel/salt-analytics-framework?style=plastic
   :target: https://pypi.org/project/salt-analytics-framework
   :alt: Python Wheel


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=plastic
   :target: https://github.com/psf/black
   :alt: Code Style: black


.. image:: https://img.shields.io/pypi/l/salt-analytics-framework?style=plastic
   :alt: PyPI - License


..
   include-starts-here

================================
What is Salt Analytics Framework
================================

This pytest plugin was extracted from `pytest-salt-factories`_. It's a collection of
of useful skip markers created to simplify and reduce code required to skip tests in
some common scenarios, for example, platform specific tests.

.. _pytest-salt-factories: https://github.com/saltstack/pytest-salt-factories


Install
=======

Installing Skip Markers is as simple as:

.. code-block:: bash

   python -m pip install salt-analytics-framework


And, that's honestly it.


Usage
=====

Once installed, you can now skip some tests with some simple pytest markers, for example.

.. code-block:: python

   import pytest

   @pytest.mark.skip_unless_on_linux
   def test_on_linux():
       assert True


Contributing
============

The salt-analytics-framework project team welcomes contributions from the community.
For more detailed information, refer to `CONTRIBUTING`_.

.. _CONTRIBUTING: https://github.com/saltstack/salt-analytics-framework/blob/main/CONTRIBUTING.md

..
   include-ends-here

Documentation
=============

The full documentation can be seen `here <https://salt-analytics-framework.readthedocs.io>`_.
