#!/bin/sh

for name in `ls *.ui`; do
    new_name="ui_"`echo $name | sed 's/\.ui/\.py/'`
    pyuic4 $name >$new_name
done
