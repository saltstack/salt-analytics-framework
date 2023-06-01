.. _changelog:

=========
Changelog
=========

Versions follow `Semantic Versioning <https://semver.org>`_ (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions with advance notice in the
**Deprecations** section of releases.

.. towncrier-draft-entries::

.. towncrier release notes start


0.5.0 (2023-06-01)
==================

Features
--------

- `#54 <https://github.com/saltstack/pytest-skip-markers/issues/54>`_: Add a Jupyter notebook processor that allows running parameterized notebooks using `papermill`



Improvements
------------

- `#46 <https://github.com/saltstack/pytest-skip-markers/issues/46>`_: Allow multiple collectors to feed data into the processors chain

- `#47 <https://github.com/saltstack/pytest-skip-markers/issues/47>`_: Forwarders always run concurrently now

- `#48 <https://github.com/saltstack/pytest-skip-markers/issues/48>`_: Create a test event collector(generator)

- `#49 <https://github.com/saltstack/pytest-skip-markers/issues/49>`_: Turn the `noop` processor into the `test` event processor(generator)

- `#50 <https://github.com/saltstack/pytest-skip-markers/issues/50>`_: Allow defining if a pipeline should restart or not when it ends or when it fails during processing.

- `#52 <https://github.com/saltstack/pytest-skip-markers/issues/52>`_: Chain processors asynchronously



Trivial/Internal Changes
------------------------

- `#47 <https://github.com/saltstack/pytest-skip-markers/issues/47>`_: Add a timed test case to verify concurrency


0.4.0 (2023-05-18)
==================

Improvements
------------

- `#41 <https://github.com/saltstack/pytest-skip-markers/issues/41>`_: AsyncIO cooperative file reads/writes. Support glob matching on paths.



Bug Fixes
---------

- `#42 <https://github.com/saltstack/pytest-skip-markers/issues/42>`_: Explicitly create a new loop and assign it to the current thread and avoid a `DeprecationWarning`

- `#43 <https://github.com/saltstack/pytest-skip-markers/issues/43>`_: Fix the seek to end of file call

- `#44 <https://github.com/saltstack/pytest-skip-markers/issues/44>`_: Import `TypedDict` from typing_extensions on Python < 3.9.2


0.3.0 (2023-05-17)
==================

Improvements
------------

- `#40 <https://github.com/saltstack/pytest-skip-markers/issues/40>`_: Allow the file collector to read from multiple files at a time


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
