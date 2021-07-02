"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
#from genologics.entities import SampleHistory
import sys
import getopt

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
	outputs = process.all_outputs(unique = True)
	indexList = []
	for o in outputs : 
		if o.type == 'Analyte' : 
			indexList.append(o.reagent_labels[0])
	
	duplicates = [x for x in indexList if indexList.count(x) > 1]
	duplicates = list(set(duplicates))
	if duplicates != [] : 
		step = Step(lims,id= args[ "stepID" ])
		
		status = "OK"
		message = "Duplicate indexes found: " + str(duplicates)

		step.program_status.status = status
		step.program_status.message = message

		step.program_status.put()

				
if __name__=='__main__':
	main()

