# Monitoring scripts

Collection of monitoring scripts. Most of them used as Nagios plugins.

## Load on the DVS

* `check_dvs_load`: check the load on a DVS server. The script reads the 1 minute load from the output of command `uptime`. Once the script has the load on the DVS server (called *node* on the script), it compares agains the thresold for *critical* or *warning*.

## Lustre

* `check_lfs_healthy`: simple script that looks for the string *not* in the file `healthy_check`. If the string is present, then there is a problem with the file system.

* `check_lfs_quota`: issue the command `lfs quota` on a file system passed as parameter. If there is a problem with the quota system, the quota information will be inside brackets "[]". If the script finds a opening bracket "[", then there is a problem, and return the status *critical* to Nagios. For example:  

```bash
    eslogin003:~ # lfs quota /univ_1
    Disk quotas for user root (uid 0):
    Filesystem  kbytes   quota   limit   grace   files   quota   limit   grace
        /univ_1 [10200224]       0       0       -   17724       0       0       -
    Some errors happened when getting quota info. Some devices may be not working or deactivated. The data in "[]" is inaccurate.
    (...)
```

* `check_ost.py`: check the usage of the Lustre OSTs. If a user submit didn't use the option to strip his job, and he wrote a lot to the disk, he could fill just one of the OST, or at least, cause a imbalance in the OST usage.

## NetApp

### Disabled cache

The `sna_wrtcache.py` scripts check if the controller has suspended the read and write caches. This can happen if the other controller has a failure. The script accepts the controller as parameter, and even the file `storage-array-profile.txt` (with `-f` option) from the support bundle. The default option is to return the `critical` status to Icinga as soon as the script finds a lun in suspended mode, but there is the option `-l` to list all volumes that are suspended.

The options to the script are:

    [root@nagiosds dbsew_summary]# ./sna_wrtcache.py --help
    Usage: sna_wrtcache.py [options]

    Options:
    -h, --help            show this help message and exit
    -p CONTROLLER_A, --primary=CONTROLLER_A
                            name of controller to query, like 'dase00-0'
    -a CONTROLLER_B, --alternative=CONTROLLER_B
                            name of seconday controller to query, like 'dase00-1'
    -f FILE_ALLVOLUMES, --file=FILE_ALLVOLUMES
                            file with the output of 'show AllVolumes'
    -l, --list            List all volumes in 'suspended' mode
    [root@nagiosds dbsew_summary]#

For example, using the `storage-array-profile.txt` file

    [root@nagiosds dbsew_summary]# ./sna_wrtcache.py -f storage-array-profile.txt
    dasw05lun00 has a write cache suspended
    [root@nagiosds dbsew_summary]#

And listing all volumes that are suspended

    [root@nagiosds dbsew_summary]# ./sna_wrtcache.py -l -f storage-array-profile.txt
    dasw05lun00  Enabled (currently suspended) Enabled (currently suspended)
    dasw05lun01  Enabled (currently suspended) Enabled (currently suspended)
    (...)

The script queries the controller for the status of the volumes

```Python
command = "SMcli " + controller + " -c 'show allVolumes;'"
pOut = subp.Popen(command, shell=True,
         stdout=subp.PIPE, universal_newlines=True)
text = pOut.communicate()[0]
```

The script then scans the variable `text` for the information about the write cache and write cache mirroring. If the script finds the word _suspended_, it return the status _critical_ to Icinga

```Python
if 'suspended' in write_cache_mirroring_status or 'suspended' in write_cache_status:
    # The write cache is suspended on the controller.
    print vol_name + " has a write cache suspended"
    sys.exit(STATE_CRITICAL)
```

The Icinga configuration is in

```bash
cat /etc/icinga/conf.d/sv_storage.cfg
(...)
# 'check-sna-wrtcache' command definition
define command{
    command_name check-sna-wrtcache
    command_line    $USER1$/check_by_ssh -H localhost -t 300 -l root  <break>
        -C "/maint/nagios/sbin/sna_wrtcache.py -p $ARG1$ -a $ARG2$"
}
(...)
define service {
   use                          critical-service-checks-5min
   hostgroup_name               storage-w,storage-e
   check_command                check-sna-wrtcache!$_HOSTC0ADDR$!$_HOSTC1ADDR$
   service_description          Check SNA write cache enabled
   service_groups               CTRL_HEALTH,all
}
[root@nagiosds conf.d]#
```

The complementary script is `wrtcache_up.sh`, that re-enable the cache. Although disabling the cache is the safest option, there is a performance penalty, and if this price becomes to high, the operator can re-enable the cache. The script takes the controller as the single parameter.

### Clock synchronization

Sometimes the clock of the controllers can get out of sync with the management workstation, and when someone logs into the controller with `SMclient`, there is a message that the clock is out of sync.

To force the synchronization, run the script `netapp_sync_clock.sh`, from the management workstation.

## GPFS

The script `check_gpfs_quota.py` checks for the `in_doubt` value of the output of the command to check quota, `mmrepquota`. The `in_doubt` value is the amount of quota that the server gave to the client, but don't know yet how much the client has already used. In case of a client failure, a new client will work with a new share from server, the share hold before the failure is still set aside in the “in doubt” value.

The script takes the fileset to be checked as parameter, but if the parameter is the word _file_, then the following argument should be the name of the file. This was done to make the development easier, since the development could be done anywhere instead of a GPFS node, and issuing real commands

```Python
    if len(sys.argv) == 1:
        print "Usage: {0} <filesystem>".format(sys.argv[0])
        sys.exit(STATE_UNKNOWN)
    else:
        # Development only. Accept the key word 'file' to read the data
        # from a file instead of running the mm command.
        if sys.argv[1] == "file":
            # read file name
            file_fs_data = sys.argv[2]
            (...)
```

The Icinga command looks like

    command_line     $USER1$/check_by_ssh -H $HOSTADDRESS$ -t 120 -l root -C "/maint/nagios/sbin/check_gpfs_quota.py gpfs.bindata"



The script checks if the amount of already used disk space plus the `in_doubt` are lower than the quota of the file system. The script also checks if the value of `in_doubt` is not too big. The threshold is defined in the `quota_check.conf` file, and it's expressed in _kilobytes_. The configuration file also has the values that should be used to control the usage of a file system. The usage is expressed as percentage quota of the file system.

``` Python
    # Calculate the usage, in percentage, of the fileset:
    usage_fs = (in_use + in_doubt)/limit_fs
    if usage_fs > usage_critical:
```

The content of the `quota_check.conf` file

```
    [root@nagiosds bin]# more quota_check.conf
    # configuration parameters for the quota check on gpfs.
    # Adjustable parameters are the values for critical and warning.
    [DEFAULT]
    # 1TB = 10^9 KB
    in_doubt_max = 1000000000

    [gpfs.bindata]
    usage_critical=0.95
    usage_warning=0.90

    [gpfs.bindata_t]
    usage_critical=0.95
    usage_warning=0.90

    [root@nagiosds bin]#
```

The script only run on the file system manager, anywhere else the script will simply exit. The test is a comparison of _hostname_ and the output of the command `mmlsmgr`:

```Python
# On the main routine
(...)
    if not is_fsmgr(quota_fileset):
        print "I'm not the file system manager for {0}".format(quota_fileset)
        sys.exit(STATE_OK)
```

