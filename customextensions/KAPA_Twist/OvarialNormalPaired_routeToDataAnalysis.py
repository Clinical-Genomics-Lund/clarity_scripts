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
	process = Process(lims, id = args[ "stepID" ])

	savedInput = []
	for inArt, output in process.input_output_maps:
		if output['output-generation-type'] == 'PerInput':
			if 'Parad - Ovarialcancer' in output['uri'].samples[0].udf[ 'Analysis' ] and output['uri'].samples[0].udf[ 'Sample Type' ] == 'Normalprov' and not re.search('Ej Godk', output['uri'].udf['Sample Classification'] ) :
				savedInput.append(inArt['uri'])

	print savedInput

	routingStage = BASEURI + "api/v2/configuration/workflows/801/stages/1936"

	print routingStage
	r = lims.route_artifacts( savedInput, stage_uri=routingStage, unassign=False)

	if r:
		print r
		sys.exit(255)

				
if __name__=='__main__':
	main()

