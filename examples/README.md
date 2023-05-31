# Examples

Example plugins for quick experimentation with Salt Analytics

## Usage

First, you'll need to install this examples extension into your salt environment targeting the root of this directory.  This could be done a couple of different ways, including `salt-pip install`, `salt-call --local pip.installed`, or however you want to get this extension into your environment.

Each of these example pipelines has their own set of requirements, but if you would like to install them all at once, you can install [all the requirements](examples/requirements/all.txt) into the same environment this extension was installed into.

### Initial Configuration

Each of these pipelines will have their own unique configuration. It is recommended that you extract them out into separate files and place them in the default include directory for your master or minion (by default, `master.d/*.conf` and `minion.d/*.conf` at the roots of the directories of the respective configuration files).

To start, if the engine is not already enabled in your configuration, you can add an `analytics-engine.conf` file populated like this...

```
engines:
  - analytics
```

This will enable the salt-analytics-framework engine to run alongside your minion or master.
## Directory Listing

Each example pipeline's instructions reside in its own directory under [pipelines](pipelines/).

- [MNIST Network](pipelines/mnist-network/README.md)
- [MNIST Notebook](pipelines/mnist-notebook/README.md)
