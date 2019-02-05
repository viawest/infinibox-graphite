'''
!/usr/bin/env python

Examples:
	Overall Performance Statistics:
 		python infinibox_hosts_workload_graphite.py
 		-u "http://<infinimetrics_fqdn>/api/rest/"
 		-F <host fqdn>
 		-C "systems/<serialnumber>/monitored_entities"
 		-f "format=json&page=last&sort=-timestamp"
 		-U "username"
 		-P "password"

Add -v to the end to view output
'''
from pprint import pformat
import time
import socket
import yaml
import functions
import global_vars
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


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
    "-F",
    "--fqdn",
    dest="fqdn",
    default=None,
    help="Specify the fqdn of the Infinibox"
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

username = options.username
password = options.password
timeout = options.timeout

url_args = ["https://{}/api/rest/hosts?fields=name,id&page_size=1000".format(
    options.fqdn
    )]
url_args.append("{}{}?{}".format(str(options.url), str(options.components), str(options.filters)))

functions.process_url(
    url_args,
    options.username,
    options.password,
    options.timeout,
    options.verbose
    )

i = 0
url_entity_id = []
host_names = []

# Associate host with entitiy id
for host in global_vars.outcome[0]:
    shortname = host["name"].split(".")
    host_names.append(shortname[0])
    for entity_id in global_vars.outcome[1]:
        if entity_id["group"] == "Hosts":
            if host["id"] == entity_id["id_in_system"]:
                monitor_entity_id = "{}{}/{}/data/?format=json&page_size=1&sort=timestamp&page=last".format(
                    options.url,
                    options.components,
                    entity_id["id"]
                    )
                url_entity_id.append(monitor_entity_id)
                '''
                functions.process_url(
                    url_args,
                    options.username,
                    options.password,
                    options.timeout,
                    options.verbose
                    )
                '''

# clear the list
del url_args[:]
del global_vars.outcome[:]

# append infinimetrics api urls
for url in url_entity_id:
    r = requests.get(
        "%s" % (url),
        verify=False,
        auth=(username, password),
        timeout=timeout
    )
    try:
        print r.json()
        url_args.append(url)
    except ValueError:
        print "Failed to decode JSON. Exluding URL."

functions.process_url(
    url_args,
    options.username,
    options.password,
    options.timeout,
    options.verbose
    )

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

# Get data to send to Graphite
timestamp = str(time.time())[0:10]

i = 0
messages = []

while i < len(global_vars.outcome):
    read_iops = str(int(global_vars.result[i]["result"][0]["read_ops"]))
    read_bytes = str(int(global_vars.result[i]["result"][0]["read_bytes"]))
    read_latency = str(int(global_vars.result[i]["result"][0]["read_latency"]))
    write_iops = str(int(global_vars.result[i]["result"][0]["write_ops"]))
    write_bytes = str(int(global_vars.result[i]["result"][0]["write_bytes"]))
    write_latency = str(int(global_vars.result[i]["result"][0]["write_latency"]))

	# Put Graphite data into list
    messages.append([
        ["{}.{}.{}.{}.{} {} {}".format(graphite_prefix, servername, "Host", host_names[i], "read_iops", read_iops, timestamp)],
        ["{}.{}.{}.{}.{} {} {}".format(graphite_prefix, servername, "Host", host_names[i], "read_bytes", read_bytes, timestamp)],
        ["{}.{}.{}.{}.{} {} {}".format(graphite_prefix, servername, "Host", host_names[i], "read_latency", read_latency, timestamp)],
        ["{}.{}.{}.{}.{} {} {}".format(graphite_prefix, servername, "Host", host_names[i], "write_iops", write_iops, timestamp)],
        ["{}.{}.{}.{}.{} {} {}".format(graphite_prefix, servername, "Host", host_names[i], "write_bytes", write_bytes, timestamp)],
        ["{}.{}.{}.{}.{} {} {}".format(graphite_prefix, servername, "Host", host_names[i], "write_latency", write_latency, timestamp)]
    ])

    i += 1

# Make connection to Graphite
conn = socket.socket()
conn.connect((graphite_address, graphite_port))

# Cycle through list items and send data to Graphit
for message in messages:
    i = 0
    while i < len(message):
        msgOutput = message[i]
        msgOutput = str(message[i]).strip("['']")
        msgOutput = "{}\n".format(msgOutput)
        print "msgOutput = {}".format(msgOutput)
        conn.sendall(msgOutput)
        i += 1

# Close connection to Graphite
conn.close()
