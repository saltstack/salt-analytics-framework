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

.. code-block:: yaml

   engines:
     - analytics


Example Pipeline
----------------

.. code-block:: yaml

   beacons:
     memusage:
       - interval: 5
       - percent: 0.01%
     status:
       - interval: 5
       - time:
         - all
       - loadavg:
         - all

   analytics:
     collectors:
       beacons-collector:
         plugin: beacons
         beacons:
           - "*"

     processors:
       noop-processor:
         plugin: noop

     forwarders:
       disk-forwarder:
         plugin: disk
         path: /var/cache/salt
         filename: events-dumped.txt
         pretty_print: true

     pipelines:
       my-pipeline:
         collect: beacons-collector
         process: noop-processor
         forward: disk-forwarder


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
.. _examples: https://github.com/saltstack/salt-analytics-framework/blob/main/examples

..
   include-ends-here

Documentation
=============

The full documentation can be seen `here <https://salt-analytics-framework.readthedocs.io>`_.


Examples
========

Some examples of custom pipelines are provided.  You can find them at `examples`_.
