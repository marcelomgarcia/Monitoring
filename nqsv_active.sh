#!/usr/bin/env bash
# Check if NQSV services are active
# Marcelo Garcia (NEC)

cmk_status=0
cmk_check="nqsv_active"
cmk_msg="${cmk_status} ${cmk_check} - OK: All NQSV services are running."

nqsv_service_list=( nqs-jsv.service nqs-lchd.service nqs-uag.service )
for ii in "${nqsv_service_list[@]}"
do
    is_active=`systemctl is-active $ii`
    if [[ "$is_active" != "active" ]]; then
        cmk_status=1
        cmk_msg="${cmk_status} ${cmk_check} - Warning: service ${ii} not active"
        break
    fi
done

echo ${cmk_msg}

exit 0
