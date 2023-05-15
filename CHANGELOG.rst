.. _changelog:

=========
Changelog
=========

Versions follow `Semantic Versioning <https://semver.org>`_ (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions with advance notice in the
**Deprecations** section of releases.

.. towncrier-draft-entries::

.. towncrier release notes start


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
