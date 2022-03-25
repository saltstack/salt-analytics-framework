# Simple Demo Of Salt Analytics

## Setup

### Build the Python Wheels

From the repository root, run the following commands:
NOTE: You may need to run the first ``python setup.py bdist_wheel`` command twice :(

```shell
python3 -m pip install wheel
python3 setup.py bdist_wheel
cd demo/data-remove-extension
python3 setup.py bdist_wheel
cd -
```

### Build Docker Container

From the repository root, run the following command:

```shell
docker build . -f demo/Dockerfile -t salt-analytics/demo
```

### Start The Container

Run the following command:
```shell
docker run -it --rm --name analytics-demo salt-analytics/demo:latest
```

### Radio Configuration Files

In ``/etc/salt/radio/`` you'll find several configuration files in the form of ``/etc/salt/radio/*.conf``.
We will use these to showcase the different features of our framework.

## The Demo

### Beacon Events Collection

Stop the minion by going to tmux's window 1(``CTRL-B n`` for next tmux window, ``CTRL-B p`` for previous tmux window),
2nd pane(``CTRL-B <down-arrow>`` go the pane bellow the current, ``CTRL-B <up-arrow>`` for the pane above) and doing a ``CTRL-C``.

To run the full demo, copy ``/etc/salt/radio/beacons.conf`` to ``/etc/salt/minion.d/``:

```shell
cp /etc/salt/radio/beacons.conf /etc/salt/minion.d/
```

Take a look at the configuration.

```shell
vim /etc/salt/minion.d/beacons.conf
```

Restart the salt minion.

```shell
salt-minion -l debug
```

Switch to window 2 and see the events being dumped.

### Log Line Collection

Switch back to the middle pane of window 1.

Stop the minion as you did before, and take out the beacons configuration file.

```shell
rm /etc/salt/minion.d/beacons.conf
```

Now, copy the logs collector config over to the ``minion.d`` directory.

```shell
cp /etc/salt/radio/logs.conf /etc/salt/minion.d/
```

Take a look at the configuration.

```shell
vim /etc/salt/minion.d/logs.conf
```

Restart the salt minion.

```shell
salt-minion -l debug
```

Open a terminal outside the container and fail to ``ssh`` into it.

```shell
ssh root@(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' analytics-demo)
```

You can use ``wrong`` as a bad password.

Switch to window 2 and see the events being dumped, and highlight the parsing and event-typing that it is capable of.

### Showcase Extensibility

Take note of the ``drain_result`` field that is being dumped with the logs collector.
Let's say we only want raw log results, and we want to remove the field ``drain_result`` from the event.
Currently there is no built-in way to do this, but we can easily write an extension using ``create-salt-extension`` from the pip-installable ``salt-extension``

First, let's stop the minion for now like we did before.
Then, we can show the file contents of the extension by

```shell
tree /etc/data-remove-extension/src/
```

Let's show what the extension looks like in Python

```shell
vim /etc/data-remove-extension/src/saltext/data_remove/processor.py
```

Let's also show how it get's picked up by Salt Analytics after a minion restart.
```shell
vim /etc/data-remove-extension/setup.cfg
```

Let's remove the old configuration files

```shell
rm /etc/salt/minion.d/logs.conf
```

Let's copy the relevant configuration file over now

```shell
cp /etc/salt/radio/logs-processed.conf /etc/salt/minion.d/
```

Take a look at the configuration.

```shell
vim /etc/salt/minion.d/logs-processed.conf
```

Restart the minion.

```shell
salt-minion -l debug
```

You should see errors in the minion logs.  This is expected!
We have configured a plugin that we don't yet have in our environment.  Let's stop the minion.

Now, let's install the needed plugin that we've developed as an extension.

```shell
python3 -m pip install /extension/*.whl
```

After it installs, let's restart the minion.

```shell
salt-minion -l debug
```

Switch back to window 2 in the container to see that the ``drain_result`` field is no longer being dumped during backfill.

### A Salt Managed Process

Finally, stop the minion, and show how a failed ``ssh`` attempt no longer results in data being dumped.

```shell
ssh root@(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' analytics-demo)
```

Salt stopped the engine when the minion configured to run it stopped.  This is expected and by design.

## Cleanup

From the ``tmux`` session, press ``CTRL-B d`` to detach, and the docker container will stop and you'll be back to your own terminal.