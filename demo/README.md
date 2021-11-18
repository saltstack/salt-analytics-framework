# Simple Demo Of Salt Analytics

## Setup

### Build Docker Container

From the repository root, run the following command:

```shell
docker build . -f demo/Dockerfile -t salt-analytics/demo
```

## Running the Demo

## Start The Container
Run the following command:
```shell
docker run -it --rm --name analytics-demo salt-analytics/demo:latest
```

When you start the container, a tmux session will be started.
The first window, named ``Salt`` will be split into 3 panes:

1. The ``salt-master`` running
2. The ``salt-minion`` running
3. An initial ``salt '*' test.ping`` command to ensure master and minions are properly communicating.

The second window, named ``Events Dumped`` will be spit into 3 panes:

1. An SSHD daemon running. Hint, the ``root`` user password is ``salt``
2. A ``tail`` command tailing the contents of a salt-analytics disk forwarder dump file. Contains all events, pretty printed.
3. A ``tail`` command tailing the contents of another salt-analytics disk forwarder dump file. Contains only events from the ``logs`` collector, not pretty printed.

### Salt Analytics Configuration Files

In ``/etc/salt/`` you'll find several configuration files prefixed with ``analytics-``, ``/etc/salt/analytics-*.conf``.

## Complete Demo

Stop the minion by going to tmux's window 1(``CTRL-B n`` for next tmux window, ``CTRL-B p`` for previous tmux window),
2nd pane(``CTRL-B <down-arrow>`` go the pane bellow the current, ``CTRL-B <up-arrow>`` for the pane above) and doing a ``CTRL-C``.

To run the full demo, copy ``/etc/salt/analytics-combined.conf`` to ``/etc/salt/minion.d/``:

```shell
cp /etc/salt/analytics-combined.conf /etc/salt/minion.d/
```

Restart the salt minion by going up in the shell history, you'll the command used to start the minion before.

Switch to window 2 and see the events being dumped.

### Attempt a failed SSH login

Try to ``ssh`` into the docker container, and provide a wrong password.

```shell
ssh root@(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' analytics-demo)
```
