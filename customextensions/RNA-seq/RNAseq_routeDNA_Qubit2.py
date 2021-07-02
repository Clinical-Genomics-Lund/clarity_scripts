"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
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
	outputs = process.all_outputs(unique=True)
	for o in outputs:
		if o.type == "ResultFile" :
			outputs.remove(o)

	routingStage = BASEURI + "api/v2/configuration/workflows/852/stages/2631"
	r = lims.route_artifacts( outputs, stage_uri=routingStage, unassign=False)
	if r :
		print r
		sys.exit(255)
				
if __name__=='__main__':
	main()

