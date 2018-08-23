#!/bin/bash
# Enable write cache on NetApp controller E-5xxx series.
# Marcelo Garcia (Marcelo.Garcia@EMEA.NEC.COM)
# April, 2018.
#


# Read the controller.
# Check if the argument (a single one, the controller) was given.
if [[ "$#" -ne 1 ]]; then
    echo "Syntax: $0 <controller>"
    exit 1
fi
CONTROLLER=$1

# Try to ping the controller.
ping -c 2 $CONTROLLER > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
    echo "Can't ping controller ${CONTROLLER}."
    exit 1
else
    echo "${CONTROLLER} pingable."
fi

# Run the commands.
echo "Setting all volumes on ${CONTROLLER} to 'writeCacheEnabled=TRUE;'"
COMMAND="SMcli ${CONTROLLER} -S -c 'set AllVolumes writeCacheEnabled=TRUE;'"
echo $COMMAND
echo ""
echo "Setting all volumes on ${CONTROLLER} to 'mirrorCacheEnabled=FALSE'"
COMMAND="SMcli ${CONTROLLER} -S -c 'set AllVolumes mirrorCacheEnabled=FALSE;'"
echo $COMMAND

# The End.
echo "Have a nice day."
exit 0
