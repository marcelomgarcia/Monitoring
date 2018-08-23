#!/usr/bin/env python
#
# Nagios plugin to get OST usage for a Lustre file system.
# Marcelo Garcia (mgarcia@cray.com)
#

import sys, subprocess
from optparse import OptionParser

def get_ost_use(lustre_list):
    """Return the uuid and use of most used OST."""
    ost_id = ""
    ost_max = 0

    for ll in lustre_list:
        ost_id = ll.strip().split()[0]
        ost_use = int(ll.strip().split()[4][:-1])
        if ost_use >= ost_max:
            ost_max = ost_use
            ost_id = ll.strip().split()[0]
    return(ost_id, ost_max)

def run_lfs_df(lustre_fs):
    """Run 'lfs df' on the Lustre file system 'lustre_fs'."""
    command = "lfs df {0} ".format(lustre_fs)
    pOut = subprocess.Popen(command, shell=True, 
                    stdout=subprocess.PIPE,
                    universal_newlines=True)
    text = pOut.communicate()[0] 
    text = text.strip().split('\n') 
    return(text)

def main(args = None):
    """Main function."""

    # Variables:
    ost_crit = 0
    ost_warn = 0
    lustre_fs = ""

    # Nagios status values.
    STATE_OK = 0
    STATE_WARNING = 1
    STATE_CRITICAL = 2
    STATE_UNKNOWN = 3

    parser = OptionParser()
    parser.add_option("-c", "--critical", type="int", dest="ost_crit")
    parser.add_option("-w", "--warning", type="int", dest="ost_warn")
    parser.add_option("-m", "--mount", type="string", dest="lustre_fs", 
            help="mount point of lustre file system")
    (options, args) = parser.parse_args()

    lustre_fs = options.lustre_fs
    ost_warn  = options.ost_warn
    ost_crit  = options.ost_crit

    if not lustre_fs or not ost_warn or not ost_crit:
        print "./check_ost.py -c <critical> -w <warning> -m <file system>"
        sys.exit(STATE_UNKNOWN)

    lustre_df = run_lfs_df(lustre_fs)
    # Cut the 'header' and 'summary line'.
    lustre_df = lustre_df[1:-2]

    # Get the most used OST.
    ost_id, ost_max = get_ost_use(lustre_df)

    # Return OST status to Nagios.
    if ost_max > ost_crit:
        print "OST CRITICAL - {0} is {1}% full".format(ost_id, ost_max)
        sys.exit(STATE_CRITICAL)
    elif (ost_crit > ost_max) and (ost_max >= ost_warn):
        print "OST WARNING - {0} is {1}% full".format(ost_id, ost_max)
        sys.exit(STATE_WARNING)
    else:
        print "OST OK - {0} is {1}% full".format(ost_id, ost_max)
        sys.exit(STATE_OK)
        
if __name__ == "__main__":
    main()
