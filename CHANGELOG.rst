.. _changelog:

=========
Changelog
=========

Versions follow `Semantic Versioning <https://semver.org>`_ (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions with advance notice in the
**Deprecations** section of releases.

.. towncrier-draft-entries::

.. towncrier release notes start


1.0.0 (2022-07-05)
==================

Features
--------

- `#22 <https://github.com/saltstack/pytest-skip-markers/issues/22>`_: Pipelines now have access to caching.

  * There's a cache(dictionary) shared among the whole pipeline where each of the ``collect``, ``process`` and ``forward`` executions can store and grab data from.
  * Additionally, each of ``collect``, ``process`` and ``forward`` plugins in a pipeline execution have their own caching, not shared. Could be used to store state between executions.



Trivial/Internal Changes
------------------------

- `#14 <https://github.com/saltstack/pytest-skip-markers/issues/14>`_: Update copyright headers
