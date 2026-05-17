#!/bin/bash
from=$1
to=$2

while ! ssh transfer rsync -rlDvuziht $from $to

do
     echo "Command failed try again in 10 min."
     sleep 10m
done

echo "Transfer complete."
