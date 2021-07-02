"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import *
import sys
import getopt
import datetime
from operator import itemgetter

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
	for output in process.all_outputs() :
		if output.name == "Input file" : 
			driver_file_out = output

	step = Step(lims,id= args[ "stepID" ])
	selected_container = step.placements.get_selected_containers()
	if selected_container[0].type.name == "8-striptubes":

		placement = step.placements.get_placement_list()
		data = [] 
		for p in placement: 
			artifact = p[0]
			sampleName = artifact.samples[0].name
			sampleLimsID = artifact.samples[0].id
			container = p[1][0]
			containerName = container.name
			position = p[1][1]
			position = position.replace("1:" , "A" ) 
			d = [containerName , position , sampleLimsID + "_" + sampleName]
			data.append(d)

		data.sort(key=itemgetter(0,1))
	
		with open("QubitFlexInput.csv", "w") as f:
			f.write("{0},{1},{2}\n".format("Plate Barcode","Well","Sample Id"))
			for d in data : 
				f.write("{0},{1},{2}\n".format(d[0] , d[1], d[2]) )
		lims.upload_new_file(driver_file_out, "QubitFlexInput.csv")

				
if __name__=='__main__':
	main()

