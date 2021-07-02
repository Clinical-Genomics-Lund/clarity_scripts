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
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:n:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-s':
			args[ "stepID" ] = p
		elif o == '-n':
			args[ "sampleName" ] = p

	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()
		
	process = Process(lims,id= args[ "stepID" ])
        outputs = process.all_outputs(unique=True)

	txt = "no"
	change = None
	o_toChange = ""

	for o in outputs : 
		if o.name == args[ "sampleName" ] : 
			o_toChange = o 
			print "## Sample ## " , o.name
			if o.udf['Variant findings'] == "NEG" : 
				change = "POS"
				txt = raw_input("Variant finding will be changed from NEG to POS.\nConfirm [yes/no]: ")


			elif o.udf['Variant findings'] == "POS" :
				change = "NEG"
				txt = raw_input("Variant finding will be changed from POS to NEG.\nConfirm [yes/no]")

			elif o.udf['Variant findings'] == "not registered" :
				change = raw_input("Variant finding is not registered.\nWhat do you want variant finding to be [POS/NEG]")
				if change not in ["POS", "NEG" ] : 
					print "Chosen variant finding must be POS or NEG. Script will be aborted"
					sys.exit(255)
				
				txt = raw_input("Variant finding will be changed from not registered to {}.\nConfirm [yes/no]".format( change ))
				

	if txt not in ["yes" , "no"] : 
		print "Confirm with yes or no. Script aborted" 
		sys.exit(255)

	if o_toChange :
		if txt == "yes" : 
			print "Confirmed"
			o_toChange.udf['Variant findings'] = change 
			r = o_toChange.put()
			print r 
			
				
if __name__=='__main__':
	main()

