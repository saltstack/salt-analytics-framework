#!/bin/sh
sleep 20
while true; do
    SLEEP=$(shuf -i 3-10 -n 1)
    sleep $SLEEP
    /usr/bin/salt \* test.fib 3
    SLEEP=$(shuf -i 3-10 -n 1)
    sleep $SLEEP
    /usr/bin/salt \* test.ping
done
