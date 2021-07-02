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

	inputs = process.all_inputs(unique = True)
	input_samples = [i.samples[0] for i in inputs ]
	date = datetime.date.today()
	for sample in input_samples :
		#set sample udf 'Workflow started (date)'
		sample.udf['Workflow started (date)'] = str( date )
		sample.put()

	savedInput = []
	for inArt, output in process.input_output_maps:
		if output['output-generation-type']=='PerInput':
			if output['uri'].udf['Skip Quantification']:
				savedInput.append(inArt['uri'])

	unassignWorkflow = BASEURI + "/api/v2/configuration/workflows/804"
	routingStage = BASEURI + "/api/v2/configuration/workflows/804/stages/2148"
	u = lims.route_artifacts( savedInput, workflow_uri=unassignWorkflow, unassign=True)
	r = lims.route_artifacts( savedInput, stage_uri=routingStage, unassign=False)

	if r or u :
		print r
		print u
		sys.exit(255)

				
if __name__=='__main__':
	main()

