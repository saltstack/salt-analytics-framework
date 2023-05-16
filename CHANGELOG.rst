.. _changelog:

=========
Changelog
=========

Versions follow `Semantic Versioning <https://semver.org>`_ (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions with advance notice in the
**Deprecations** section of releases.

.. towncrier-draft-entries::

.. towncrier release notes start


0.2.0 (2023-05-16)
==================

Improvements
------------

- `#31 <https://github.com/saltstack/pytest-skip-markers/issues/31>`_: Refactored the logs collector into a generic file collector

- `#33 <https://github.com/saltstack/pytest-skip-markers/issues/33>`_: If a processor decides not to return the passed event, no attempts to run the next processor on it or just forward it should be made

- `#34 <https://github.com/saltstack/pytest-skip-markers/issues/34>`_: Log the traceback on the first time a pipeline run raises an exception

- `#37 <https://github.com/saltstack/pytest-skip-markers/issues/37>`_: Processors can now return 1 or more events, they'll all get forwarded



Bug Fixes
---------

- `#32 <https://github.com/saltstack/pytest-skip-markers/issues/32>`_: If one of the processors raises an exception, stop processing the event


0.1.1 (2023-05-15)
==================

Improvements
------------

- `#30 <https://github.com/saltstack/pytest-skip-markers/issues/30>`_: The `CollectedEvent.data` type is now `Mapping` instead of `Dict`. This allows to use `TypedDict`'s for that attribute.



Trivial/Internal Changes
------------------------

- `#29 <https://github.com/saltstack/pytest-skip-markers/issues/29>`_: Start testing against Salt's onedir archives.

- `#30 <https://github.com/saltstack/pytest-skip-markers/issues/30>`_: Fix `.pre-commit-config.yaml` headers


0.1.0 (2023-04-28)
==================

First public release of the project.
