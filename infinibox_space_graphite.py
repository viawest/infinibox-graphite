'''
Examples:
    python infinibox_space_graphite.py
    -F "<InfiniBox fqdn>"
    -U "username"
    -P "password"
'''

from __future__ import division
from pprint import pformat
import requests
import functions
import global_vars
from infinisdk import InfiniBox
import time
import socket
import yaml

global_vars.size = ""

# define and gather command line options
parser = functions.ArgumentParserEx(
	prog="check_infinidat",
	description="Utilizes the Infinibox API to check status of monitored hardware and services.",
)

parser.add_argument(
	"-F",
	"--fqdn",
	dest="fqdn",
	default=None,
	help="Specify the fqdn of the Infinibox"
)

parser.add_argument(
	"-u",
	"--url",
	dest="url",
	default=None,
	help="Specify the location of the Infinibox API. (default: %(default)s)"
)

parser.add_argument(
	"-U",
	"--username",
	dest="username",
	default=None,
	help="Username to use when connecting to API. (default: %(default)s)"
)

parser.add_argument(
	"-P",
	"--password",
	dest="password",
	default=None,
	help="Password to use when connecting to API. (default: %(default)s)"
)

parser.add_argument(
	"-t",
	"--timeout",
	dest="timeout",
	default=10,
	type=int,
	help="Time in seconds plugin is allowed to run. (default: %(default)s)"
)

parser.add_argument(
	"-v",
	"--verbose",
	action="store_true",
	dest="verbose",
	default=False,
	help="Turn on verbosity."
)

# parse arguments
options = parser.parse_args()

# show command line options
if options.verbose:
	# store password temporarily
	password = options.password

	# hide password from output
	options.password = "xxxxxx"

	# show command line options
	print "command line options:\n%s\n" % (pformat(vars(options)))

	# restore password
	options.password = password

global_vars.system = InfiniBox(options.fqdn, auth=(options.username, options.password))

global_vars.system.login()

state = 0
total = 0
hosts = global_vars.system.hosts
vols = global_vars.system.volumes
pools = global_vars.system.pools
luns = global_vars.system.luns
clusters = global_vars.system.host_clusters
total_space_allocated = 0
total_space_used = 0
i = 0 # For loop iterator

# build proper message
state, message = functions.build_response(state)

# override message and state if running in verbose mode
if options.verbose:
	state = functions.UNKNOWN
	message = "UNKNOWN:"

# List clusters and their associated hosts
for cluster in clusters:
	i = 0 # iteration varialbe for the for loop
	cluster_hosts = str(cluster.get_hosts())
	cluster_hosts = cluster_hosts.split(",")
	cluster_name = cluster.get_name()
	while i < len(cluster_hosts):
		cluster_host = str(cluster_hosts[i][10:15])
		for host in hosts:
			if str(host.get_id()) == cluster_host:
				host_name = host.get_name()
		i += 1
	
# List volumes along with their storage stats(size, used) and storage pool association
for vol in vols:
	vol_id = str(vol.get_pool())
	vol_id_start = vol_id.find("=") + 1
	vol_id_end = len(vol_id) -1
	vol_space_used = "volumes?fields=used&id=eq:{}".format(vol.get_id())
	vol_name = vol.get_name()
	
	# Get space used for volume
	functions.response_manipulation("Volume", "used", vol_space_used)

	# Get space allocated for volume
	vol_size = "volumes?fields=size&id=eq:{}".format(vol.get_id())
	functions.response_manipulation("Volume", "allocated", vol_size)
	for pool in pools:
		if str(pool.get_id()) == str(vol_id[vol_id_start:vol_id_end]):
			vol_pool_name = pool.get_name()
			functions.response_manipulation("Volume", "Capacity", vol_size)
			size_cap = global_vars.size
			functions.response_manipulation("Volume", "Used", vol_space_used)
			size_available = size_cap - global_vars.size
			# Add up space used
			total_space_allocated = total_space_allocated + size_cap
			total_space_used = total_space_used + global_vars.size

total_space_used = total_space_used /1000		
	
response = global_vars.system.api.get("system/capacity/total_physical_capacity")
sys_phys_cap = response.get_result() / 1000 /1000 /1000 /1000

response = global_vars.system.api.get("system/capacity/total_virtual_capacity")
sys_virt_cap = response.get_result() / 1000 /1000 /1000 /1000

# Calculate physical capacity and allocation from the pool level
size_phys_alloc = 0

for pool in pools:
	pool_phys_space_alloc = "pools?fields=allocated_physical_space&id=eq:{}".format(pool.get_id())
	functions.response_manipulation("Pool", "allocated", pool_phys_space_alloc)
	size_phys_alloc = size_phys_alloc + global_vars.size
	
avail_phys_cap = sys_phys_cap - size_phys_alloc / 1000
phys_space_allocated = sys_phys_cap - avail_phys_cap

# Calculate virtual capacity from the pool level
global_vars.size = ""
size_virt_cap = 0

for pool in pools:
	pool_virt_space_cap = "pools?fields=virtual_capacity&id=eq:{}".format(pool.get_id())
	functions.response_manipulation("Pool", "capacity", pool_virt_space_cap)
	size_virt_cap = size_virt_cap + global_vars.size

size_virt_cap = size_virt_cap / 1000

# Calculate virtual free space at the pool level
global_vars.size = ""
size_virt_free = 0
pool_virt_space_used = 0

for pool in pools:
	pool_virt_space_free = "pools?fields=free_virtual_space&id=eq:{}".format(pool.get_id())
	functions.response_manipulation("Pool", "available", pool_virt_space_free)
	size_virt_free = size_virt_free + global_vars.size
	
size_virt_free = size_virt_free / 1000
virt_space_allocated = size_virt_cap - size_virt_free
virt_space_free = sys_virt_cap - virt_space_allocated

############################
# Start Graphite Send Code #
############################

i = 0 # reset iterator variable to zero

# Define Graphite information
with open("settings.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

for section in cfg:
    if options.fqdn.split(".")[1].find(section) != -1:
        graphite_address = str(cfg[options.fqdn.split(".")[1]]["graphite_address"])
        graphite_port = cfg[options.fqdn.split(".")[1]]["graphite_port"]
        graphite_prefix = cfg[options.fqdn.split(".")[1]]["graphite_prefix"]
        graphite_timeout = cfg[options.fqdn.split(".")[1]]["graphite_timeout"]

'''
print "graphite_address={}".format(graphite_address)
print "graphite_port={}".format(graphite_port)
print "graphite_prefix={}".format(graphite_prefix)
print "graphite_timeout={}".format(graphite_timeout)
print ""
'''

servername = options.fqdn.split(".")[0]

# Get timestamp to send to Graphite
timestamp = str(time.time())[0:10]

# Put Graphite data into list
message = [["{}.{}.{} {:.3f} {}".format(graphite_prefix, servername, "total_phys_space_allocated", (phys_space_allocated), timestamp)],
 ["{}.{}.{} {:.3f} {}".format(graphite_prefix, servername, "total_virt_space_allocated", (virt_space_allocated), timestamp)],
 ["{}.{}.{} {:.3f} {}".format(graphite_prefix, servername, "total_phys_space_capacity", sys_phys_cap, timestamp)],
 ["{}.{}.{} {:.3f} {}".format(graphite_prefix, servername, "total_phys_space_available", avail_phys_cap, timestamp)],
 ["{}.{}.{} {:.3f} {}".format(graphite_prefix, servername, "total_virt_space_capacity", sys_virt_cap, timestamp)],
 ["{}.{}.{} {:.3f} {}".format(graphite_prefix, servername, "total_virt_space_available", virt_space_free, timestamp)],
 ["{}.{}.{} {:.3f} {}".format(graphite_prefix, servername, "total_phys_space_used", total_space_used, timestamp)]]
 
 # Make connection to Graphite
conn = socket.socket()
conn.connect((graphite_address, graphite_port))

# Cycle through list items and send data to Graphite
while (i < len(message)):
    msgOutput = message[i]
    msgOutput = str(message[i]).strip("['']")
    msgOutput = "{}\n".format(msgOutput)
    print msgOutput
    conn.sendall(msgOutput)
    i = i + 1
	
# Close connection to Graphite
conn.close()
