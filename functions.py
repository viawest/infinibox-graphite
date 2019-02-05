from pprint import pformat
import requests
import global_vars
import sys
import argparse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# exit codes
OK       = 0
WARNING  = 1
CRITICAL = 2
UNKNOWN  = 3

# Disabled SSL certificate warnings for http api requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def process_url(api_url, username, password, timeout, verbose):
    ''' process API urls individually for each object'''
    #global i
    i = 0 # For loop iterator
    r = []
    global_vars.result = []
    global_vars.outcome = []

    while i < len(api_url):
        try:
	    # make request
            r.append(requests.get(
                "%s" % (api_url[i]),
                verify=False,
                auth=(username, password),
                timeout=timeout
            ))
        except Exception as message:
            print "r{}".format(i)
            print "CRITICAL: Could not get data when querying the Infinibox (%s)" % (message)
            exit(CRITICAL)

	# show raw results
        if verbose:
            print "Raw result:\n%s\n" % (r[i].text)

	# exit if there was a bad status code
        if r[i].status_code != 200:
            print "r{}".format(i)
            print "CRITICAL: Could not get data when querying the Infinibox which returned (%d)" % (r[i].status_code)
            exit(CRITICAL)

	# decode the json
        global_vars.result.append(r[i].json())

	# show decoded json
        if verbose:
            print "Decoded json:\n%s\n" % (pformat(global_vars.result[i]))

        state = 0

	# build proper message
        state, message = build_response(state)

	# override message and state if running in verbose mode
        if verbose:
            state = UNKNOWN
            message = "UNKNOWN:"

	# evaluate returned data from API calls
        global_vars.outcome.append(global_vars.result[i]["result"])

        i += 1


# String manipulation for space utilization output	
def response_manipulation(storage_type ,space_type, response_string):
	response = global_vars.system.api.get(response_string)
	response = str(response.get_result())
	response_start = response.find(":") + 2
	response_end = response.find("L")
	response = response[response_start:response_end]
	response = int(response.strip("}")) // 1000000000
	global_vars.size = response


def build_response(state):
    """ Builds proper monitoring response based on exit code.
    """
    if state == OK:
        message = "OK:"
    elif state == WARNING:
        message = "WARNING:"
    elif state == CRITICAL:
        message = "CRITICAL:"
    else:
        state = UNKNOWN
        message = "UNKNOWN:"

    return(state, message)

class ArgumentParserEx(argparse.ArgumentParser):
    """ Version of argparse that exits properly for monitoring plugins.
    """
    def exit(self, status=None, message=None):
        if message:
            self._print_message(message, sys.stderr)

        if status is not None:
            sys.exit(status)

        sys.exit(UNKNOWN)
