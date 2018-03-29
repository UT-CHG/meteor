#!/bin/bash

if [ "$#" -eq "0" ]; then
    cmd="yapf -i --style=.style *.py */*.py */*/*.py */*/*/*.py */*/*/*/*.py"
    echo ${cmd}
    ${cmd}
else
    for var in "$@"
    do
	cmd="yapf -i --style=.style ${var}"
	echo ${cmd}
	${cmd}
    done
fi
