#!/usr/bin/env python
# Check the status of the NetApp controller write cache. 
# After a controller failure, the partner can 'suspend' the write cache.
# Marcelo Garcia (marcelo.garcia@emea.nec.com)
# March/2018.

import sys, tempfile
import subprocess as subp
from optparse import OptionParser


def ping_node(node):
    """Ping 'node', returns 'true' if 'node' is reachable."""

    # Create a temporary file for 'stdout', otherwise 'call' will print 
    # the output on the screen, and I don't like that. I just want the exit
    # status. The 'stderr' is redirect to 'stdout'.
    ftmp = tempfile.TemporaryFile()
    ping_cmd = ['ping', '-c 3', node]
    isping = subp.call(ping_cmd,stdin=None, stdout=ftmp,stderr=subp.STDOUT)
    # The temporary file is deleted when it's closed
    ftmp.close()

    # Return 'true' if ping was OK (value '0').
    return isping == 0

def read_AllVolumes(file_volumes):
    """Reads a file generated by smcli command 'show AllVolumes' and returns the
	   content of the file."""
    
    # If the file doesn't exist, print a message instead of crashing the script. 
    try:
        fin = open(file_volumes, 'r')
    except IOError:
        print "File " + file_volumes + " not found (IOError)"
        sys.exit(STATE_UNKNOWN)
    except:
        print "Something went wrong here. Invalid file?"
        sys.exit(STATE_UNKNOWN)
    else:
        # Everything is OK with the file.
        text = fin.readlines()
        fin.close()

    # Remove the 'line break' (\n) character from the text.
    text = [line.strip() for line in text]

    return text

def get_AllVolumes(controller, secondary=None):
    """Run smcli command 'show AllVolumes' on the controller, the output is 
       returned to the calling function. 
       The primary controller (a) is mandatory, but the secondary controller 
       (b) is optional."""

    # Check which controller is reachable.
    if not ping_node(controller):
        # The ping to the primary controller failed. Trying the secondary,
        # if it was specified.
        if secondary:
            if ping_node(secondary):
                # Good, the second controller is accessible. We can continue.
                controller = secondary
            else:
                # Bad, the second controller is not reachable too.
                print "Both controllers: " + controller + " and " + secondary + " are unreachable. Aborting..."
                sys.exit(STATE_UNKNOWN)
        else:
            print "Primary controller unreachable and no secondary was given. Aborting..."
            sys.exit(STATE_UNKNOWN)

    # OK. If we are here, I assume we have one controller to query.
    command = "SMcli " + controller + " -c 'show allVolumes;'"
    pOut = subp.Popen(command, shell=True, 
                    stdout=subp.PIPE, universal_newlines=True)
    text = pOut.communicate()[0] 

    text = text.strip().split('\n') 
    
    return(text)
    
if __name__ == "__main__":
    # Variables.
    controller_a = ""  # Primary controller, and...
    controller_b = ""  # secondary one.
    file_AllVolumes = ""
    vol_name = ""
    write_cache_status = ""
    write_cache_mirroring_status = ""

    # Nagios status values.
    STATE_OK = 0
    STATE_WARNING = 1
    STATE_CRITICAL = 2
    STATE_UNKNOWN = 3

    # Process command line arguments.
    parser = OptionParser()
    parser.add_option("-p", "--primary", type="string", dest="controller_a", 
            help="name of controller to query, like 'dase00-0'")
    parser.add_option("-a", "--alternative", type="string", dest="controller_b", 
            help="name of secondary controller to query, like 'dase00-1'")
    parser.add_option("-f", "--file", type="string", dest="file_AllVolumes", 
            help="file with the output of 'show AllVolumes'")
    (options, args) = parser.parse_args()

    # Extract the values from the parser.
    controller_a = options.controller_a
    controller_b = options.controller_b
    file_AllVolumes = options.file_AllVolumes

    # Check if the parameters are correct. 
    # We need a file or a controller, not both or none.
    if not controller_a and not file_AllVolumes:
        print sys.argv[0] + " controller|[secondary]|file, give controller or file."
        sys.exit(STATE_UNKNOWN)
    elif controller_a and file_AllVolumes:
        print sys.argv[0] + " controller|[secondary]|file, give controller or file, not both."
        sys.exit(STATE_UNKNOWN)
    elif controller_a:
        if controller_b:
            text = get_AllVolumes(controller_a, controller_b)
        else:
            text = get_AllVolumes(controller_a)
    else:
        text = read_AllVolumes(file_AllVolumes)

    # Now we process the data from the controller.
    for line in text:
        if 'Volume name' in line:
            vol_name = line.split(':')[1].strip()
        if 'Write cache' in line:
            write_cache_status = line.split(':')[1].strip()
        if 'Write cache with mirroring' in line:
            write_cache_mirroring_status = line.split(':')[1].strip()
        if vol_name and write_cache_status and write_cache_mirroring_status:
            if 'suspended' in write_cache_mirroring_status or 'suspended' in write_cache_status:
                # The write cache is suspended on the controller.
                print vol_name + " has a write cache suspended"
                sys.exit(STATE_CRITICAL)
            else:
                vol_name = ""
                write_cache_status = ""
                write_cache_mirroring_status = ""
    else:
        print "All write caches are fully enabled."
        sys.exit(STATE_OK)
