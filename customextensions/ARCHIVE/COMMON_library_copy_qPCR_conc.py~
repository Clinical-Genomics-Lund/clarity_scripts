"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
#from genologics.entities import SampleHistory
import sys
import getopt
import datetime

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
	inouts = process.input_output_maps 
	resultfilesPerInput = [io for io in inouts if io[1]['output-generation-type'] == 'PerInput']
	resultfilesPerInput_uri = [io[1]['uri'] for io in resultfilesPerInput]
	#date = process.date_run "Comment: does not work until step is completed
	date = datetime.date.today()
	
	for o in resultfilesPerInput_uri :
		if len(o.samples) == 1 : 
			conc = float( o.udf['Qubit concentration (ng/ul)'] )
			sample = o.samples[0]
			#set sample udfs
			sample.udf['Library concentration (ng/ul)'] = conc
			sample.udf['Library concentration (date)'] = str(date)
			sample.put()

				
if __name__=='__main__':
	main()

