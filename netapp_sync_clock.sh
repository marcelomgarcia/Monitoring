#!/bin/bash
# Synchronize the Netapp controller clock with the management station, "nagiosds"
# Marcelo Garcia (marcelo.garcia@emea.nec.com)
# May/2018.
#
# Usage:
# [root@nagiosds bin]# crontab -l
# *   3 * * * /maint/netapp/netapp_sync_clock.sh > /root/marcelo/logs/netapp_clock.log 2>&1
#

function sync_clock {
    PREFIX=$1
    COUNT=$2

    for ii in `seq 0 $((COUNT))`; do
        CONTROLLER=`printf "${PREFIX}%02i" ${ii}`
        HOSTNAME_A="${CONTROLLER}-0"
        HOSTNAME_B="${CONTROLLER}-1"
        echo "${CONTROLLER} current clock:"
        SMcli ${HOSTNAME_A} -S -c "show storageArray time;"
        echo "nagiosds current time: `date`"
        echo "Synchronizing clock on ${HOSTNAME_A}"
        SMcli ${HOSTNAME_A} -S -c "set storageArray time;"
        echo "Synchronizing clock on ${HOSTNAME_B}"
        SMcli ${HOSTNAME_B} -S -c "set storageArray time;"
        echo "${CONTROLLER} clock after synchronization:"
        SMcli ${HOSTNAME_A} -S -c "show storageArray time;"
        echo ""
        echo ""
    done
}

# Main routine.

echo "#"
echo "# DBSE"
echo "#"
sync_clock dbse 2

echo "#"
echo "# DASE"
echo "#"
sync_clock dase 7

echo "#"
echo "# DBSW"
echo "#"
sync_clock dbsw 2

echo "#"
echo "# DASW"
echo "#"
sync_clock dasw 7

echo "Have a nice day."
