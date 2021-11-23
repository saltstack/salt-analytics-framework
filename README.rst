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

It's a framework which extends `Salt`_ through the use of an `engine`_ that can collect,
process and forward analytics/metrics data.


Install
=======

Installing Salt Analytics Framework is as simple as:

.. code-block:: bash

   python -m pip install salt-analytics-framework


Configuration
=============

The minimal configuration to start salt analytics with `Salt`_ is to add it to Salt's engines
configuration:

.. literalinclude:: demo/analytics-beacons.conf
   :name: /etc/salt/minion
   :lines: 1,2

   engines:
     - analytics

Example Pipeline
----------------

.. literalinclude:: demo/analytics-beacons.conf
   language: yaml
   :name: /etc/salt/analytics
   :lines: 4-


Usage
=====

TBD

Contributing
============

The salt-analytics-framework project team welcomes contributions from the community.
For more detailed information, refer to `CONTRIBUTING`_.

.. _salt: https://github.com/saltstack/salt
.. _engine: https://docs.saltproject.io/en/latest/topics/engines/index.html
.. _CONTRIBUTING: https://github.com/saltstack/salt-analytics-framework/blob/main/CONTRIBUTING.md

..
   include-ends-here

Documentation
=============

The full documentation can be seen `here <https://salt-analytics-framework.readthedocs.io>`_.
