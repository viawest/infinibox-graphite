'''
Examples: 
    Overall Performance Statistics:
        python infinibox_workload_graphite.py
        -u "http://<infinimetrics_fqdn>/api/rest/"
        -s "<InfiniBox hostname>"
        -C "systems/<serial#>/monitored_entities/1/data"
        -f "format=json&page=last&page_size=1&sort=-timestamp"
        -U "username"
        -P "password"

Add -v to the end to view output
'''

from pprint import pformat
import requests
import time
import logging
import socket
import yaml
import functions

# define and gather command line options
parser = functions.ArgumentParserEx(
	prog="check_infinidat",
	description="Utilizes the Infinibox API to check status of monitored hardware and services.",
)

parser.add_argument(
	"-u",
	"--url",
	dest="url",
	default=None,
	help="Specify the location of the Infinibox API. (default: %(default)s)"
)

parser.add_argument(
	"-s",
	"--servername",
	dest="servername",
	default=None,
	help="Specify the short name of the Infinibox. (default: %(default)s)"
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
	"-C",
	"--components",
	dest="components",
	default=None,
	required=True,
	help="Name of component to appent to url."
)

parser.add_argument(
	"-f",
	"--filters",
	dest="filters",
	default=None,
	required=True,
	help="Result filters to appent to url."
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

print " "

url_args = "{}{}?{}".format(str(options.url), str(options.components), str(options.filters))

try:
	# make request
	r = requests.get(
		"%s" % (url_args),
		auth=(options.username, options.password),
		timeout=options.timeout
	)
except Exception as message:
	print "CRITICAL: Could not get data when querying the Infinibox (%s)" % (message)
	exit(functions.CRITICAL)

# show raw results
if options.verbose:
	print "Raw result:\n%s\n" % (r.text)

# exit if there was a bad status code
if r.status_code != 200:
	print "CRITICAL: Could not get data when querying the Infinibox which returned (%d)" % (r.status_code)
	exit(functions.CRITICAL)

# decode the json
result = r.json()

# show decoded json
if options.verbose:
	print "Decoded json:\n%s\n" % (pformat(result))

state = 0
total = 0
i1 = 0
i2 = 0
i = 0

# build proper message
state, message = functions.build_response(state)

# override message and state if running in verbose mode
if options.verbose:
	state = functions.UNKNOWN
	message = "UNKNOWN:"

# evaluate returned data from API calls
outcome = result["result"]	

# Define Graphite information
with open("settings.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

for section in cfg:
    if options.url.split(".")[1].find(section) != -1:
        graphite_address = str(cfg[options.url.split(".")[1]]["graphite_address"])
        graphite_port = cfg[options.url.split(".")[1]]["graphite_port"]
        graphite_prefix = cfg[options.url.split(".")[1]]["graphite_prefix"]
        graphite_timeout = cfg[options.url.split(".")[1]]["graphite_timeout"]

'''
print "graphite_address={}".format(graphite_address)
print "graphite_port={}".format(graphite_port)
print "graphite_prefix={}".format(graphite_prefix)
print "graphite_timeout={}".format(graphite_timeout)
print ""
'''

servername = options.servername

# Get data to send to Graphite
timestamp = str(time.time())[0:10]
read_iops = str(int(outcome[0]["read_ops"]))
read_bytes = str(int(outcome[0]["read_bytes"]))
read_latency = str(int(outcome[0]["read_latency"]))
write_iops = str(int(outcome[0]["write_ops"]))
write_bytes = str(int(outcome[0]["write_bytes"]))
write_latency = str(int(outcome[0]["write_latency"]))
total_iops = int(outcome[0]["read_ops"]) + int(outcome[0]["write_ops"])
total_bytes = int(outcome[0]["read_bytes"]) + int(outcome[0]["write_bytes"])

# Print out performance data
message = [["{}.{}.{} {} {}".format(graphite_prefix, servername, "read_iops", read_iops, timestamp)],
 ["{}.{}.{} {} {}".format(graphite_prefix, servername, "read_bytes", read_bytes, timestamp)],
 ["{}.{}.{} {} {}".format(graphite_prefix, servername, "read_latency", read_latency, timestamp)],
 ["{}.{}.{} {} {}".format(graphite_prefix, servername, "write_iops", write_iops, timestamp)],
 ["{}.{}.{} {} {}".format(graphite_prefix, servername, "write_bytes", write_bytes, timestamp)],
 ["{}.{}.{} {} {}".format(graphite_prefix, servername, "write_latency", write_latency, timestamp)],
 ["{}.{}.{} {} {}".format(graphite_prefix, servername, "total_iops", total_iops, timestamp)],
 ["{}.{}.{} {} {}".format(graphite_prefix, servername, "total_bytes", total_bytes, timestamp)]] 
 
conn = socket.socket()
conn.connect((graphite_address, graphite_port))

while (i < len(message)):
    msgOutput = message[i]
    msgOutput = str(message[i]).strip("['']")
    msgOutput = "{}\n".format(msgOutput)
    print msgOutput
    conn.sendall(msgOutput)
    i = i + 1
	
conn.close()
			