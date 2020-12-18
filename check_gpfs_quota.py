#!/usr/bin/env python
# Check quota of the GxFS file system:
# OK if "KB" + "in_doubt" < "quota".
# Also check if the "in_doubt" it's not too big > 1TB.
# Marcelo Garcia
# Nov/2018.
#

import sys
import tempfile
import platform
import subprocess as subp
import ConfigParser as cfgp

# Nagios/Icinga exit codes.
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3

# Environment
BASE_DIR="/maint/nagios"
BIN_DIR=BASE_DIR + "/sbin"
ETC_DIR=BASE_DIR + "/etc"

def is_fsmgr(fileset):
    """Check if the node is the manager"""

    # Get hostname.
    node_name = platform.node()

    # Get file system manager
    command = "mmlsmgr {0} ".format(fileset)
    pOut = subp.Popen(command, shell=True, stdout=subp.PIPE,
                    universal_newlines=True)
    text = pOut.communicate()[0] 
    text = text.strip().split('\n') 

    # We just want the third field of the last line.
    line = text[-1].split()[2]
    # Ignoring the first and last characters, '(' and ')'.
    fsmanager = line[1:-1]

    if node_name == fsmanager:
        return True
    else:
        return False

def read_quota_file(file_quota):
    """Read the quota information from a file generated with the command
    'mmrepquota -j <fileset>."""
    fin = open(file_quota,'r')
    text = fin.readlines()
    fin.close()

    # Remove some control characters from the input.
    text = [line.strip() for line in text]

    return text

def read_quota_cmd(fileset):
    """Read quota information issuing command 'mmrepquota -j <fileset>'"""

    command = "mmrepquota -j {0} ".format(fileset)
    pOut = subp.Popen(command, shell=True, stdout=subp.PIPE,
                    universal_newlines=True)
    text = pOut.communicate()[0] 
    # Remove control characters (and trailing spaces) and break the lines
    # at the new-line to looks like on the terminal or reading from a file.
    text = text.strip().split('\n') 

    return text

if __name__ == "__main__":
    # The filesystem to check is an argument to the script: argv[1]
    if len(sys.argv) == 1:
        print "Usage: {0} <filesystem>".format(sys.argv[0])
        sys.exit(STATE_UNKNOWN)
    else:
        # Development only. Accept the key word 'file' to read the data
        # from a file instead of running the mm command.
        if sys.argv[1] == "file":
            # read file name
            file_fs_data = sys.argv[2]
            is_devel = True
            quota_fileset = 'gpfs.bindata'
        else:
            quota_fileset = sys.argv[1]
            is_devel = False

    # Read the configuration file.
    quota_config = cfgp.ConfigParser()
    try:
        quota_config.read(ETC_DIR + "/quota_check.conf")
        usage_critical = quota_config.getfloat(quota_fileset, \
                'usage_critical')
        usage_warning  = quota_config.getfloat(quota_fileset, \
                'usage_warning')
        in_doubt_max = quota_config.getint(quota_fileset, 'in_doubt_max')
    except cfgp.NoSectionError:
        print "Fileset {0} not found.".format(quota_fileset)
        sys.exit(STATE_UNKNOWN)
    except cfgp.Error:
        # Catch any other error.
        print "Something went wrong reading config file."
        sys.exit(STATE_UNKNOWN)
        
    # Check if the script is runninig on the manager of the file system.
    if not is_fsmgr(quota_fileset):
        print "I'm not the file system manager for {0}".format(quota_fileset)
        sys.exit(STATE_OK)

    # Read the quota information.
    # Reading from the file was done more during development.
    if is_devel:
        quota_txt = read_quota_file(file_fs_data)
    else:
        quota_txt = read_quota_cmd(quota_fileset)

    # Removing the header of the quota information, that is the first two
    # lines.
    quota_txt = quota_txt[2:]

    # Process quota information.
    for line in quota_txt:
        line = line.split()
        fileset = line[0]
        in_use = float(line[3])
        limit_fs = float(line[5])
        in_doubt = float(line[6])
        if int(limit_fs) == 0:
            # Skip test if fileset has no quota.
            continue
        else:
            # check the value of "in_doubt". Alert if bigger than
            # 1TB (10^12).
            # Calculate the usage, in percentage, of the fileset:
            usage_fs = (in_use + in_doubt)/limit_fs
            if usage_fs > usage_critical:
                if in_doubt >= in_doubt_max:
                    print "{0} usage is critial {1:.2%}".format(fileset, \
                      usage_fs) + " and 'in_doubt' is {0} KB (max: {1})\
                      ".format(in_doubt,in_doubt_max)
                else:
                    print "{0} usage is critial {1:.2%}".format(fileset, 
                       usage_fs)
                sys.exit(STATE_CRITICAL)
            if usage_critical > usage_fs and usage_fs > usage_warning:
                if in_doubt >= in_doubt_max:
                    print "{0} usage is high {1:.2%} and 'in_doubt' is {1} KB\
                           (max: {2})".format(fileset, usage_fs, in_doubt,\
                           in_doubt_max)
                else:
                    print "{0} usage is high {1:.2%}".format(fileset, usage_fs)
                sys.exit(STATE_WARNING)
            if in_doubt >= in_doubt_max:
                print "{0} 'in_doubt' is {1} KB (max: {2})".format(\
                    fileset, in_doubt, in_doubt_max)
                sys.exit(STATE_WARNING)
    else:
        print "Quota on all filesets is OK"
        sys.exit(STATE_OK)

    # The End.
    # Have a nice day.

