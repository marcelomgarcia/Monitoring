# Monitoring scripts

Collection of monitoring scripts. Most of them used as Nagios plugins.

## Load on the DVS

On a Cray XC system, the load on the DVS server is important. First things first, the DVS is similar to a NFS server. It projects external file systems to the compute nodes using the Cray high-speed network.

The script reads the 1 minute load from the output of command `uptime`. Once the script has the load on the DVS server (called *node* on the script), it compares agains the thresold for *critical* or *warning*.

## Lustre

* `check_lfs_healthy`: simple script that looks for the string *not* in the file `healthy_check`. If the string is present, then there is a problem with the file system.

* `check_lfs_quota`: issue the command `lfs quota` on a file system passed as parameter. If there is a problem with the quota system, the quota information will be inside brackets "[]". If the script finds a opening bracket "[", then there is a problem, and return the status *critical* to Nagios. For example:  

    eslogin003:~ # lfs quota /univ_1
    Disk quotas for user root (uid 0):
         Filesystem  kbytes   quota   limit   grace   files   quota   limit   grace
            /univ_1 [10200224]       0       0       -   17724       0       0       -
    Some errors happened when getting quota info. Some devices may be not working or deactivated. The data in "[]" is inaccurate.
    (...)

* `check_ost.py`: check the usage of the Lustre OSTs. If a user submit didn't use the option to strip his job, and he wrote a lot to the disk, he could fill just one of the OST, or at least, cause a imbalance in the OST usage.
