"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import datetime
import re

def main():
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-s':
			args[ "stepID" ] = p

	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()
	process = Process(lims,id= args[ "stepID" ])

	savedOutput = []
	savedInput = []

	for inArt, outArt in process.input_output_maps :
		if outArt['output-generation-type']=='PerInput':
			savedOutput.append(outArt['uri'])
		savedInput.append(inArt['uri'])

	workflowURI = BASEURI + "api/v2/configuration/workflows/855"
	u = lims.route_artifacts( savedInput, workflow_uri=workflowURI, unassign=True)

	if u :
		print u
		sys.exit(255)


if __name__=='__main__':
	main()

