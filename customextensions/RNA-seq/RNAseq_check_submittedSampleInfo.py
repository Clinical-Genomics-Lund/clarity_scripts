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
	inputs = process.all_inputs(unique=True)
	
	analysis_fields = { 
		'TruSeq Stranded mRNA' : ['Tissue' ],
		'TruSeq Stranded mRNA - Fusion' : ['Tissue' , 'Diagnosis'], 
		'TruSeq Stranded mRNA - Bladder' : ['Tissue'] , 
		'TruSeq Stranded mRNA - Expression - Breast' : ['Tissue' , 'SCAN-B ID' ]
		}

	family = {}
	for i in inputs : 
		#stop invalid sample names
		characters = r"_/\ ?.%*"		
		if ( any(elem in i.name for elem in characters) == True) : 
			print "Please check sample " , i.name , ".The folowing charachters are not allowed _/\ ?.%*"
			sys.exit(255)
		#Check scanB 
		if ('SCAN-B ID' in i.samples[0].udf ) :
			if ( any(elem in i.samples[0].udf['SCAN-B ID'] for elem in characters) == True) :
				print "Please check SCAN-B ID for sample " , i.name , ".The folowing charachters are not allowed _/\ ?.%*"
				sys.exit(255)

		#check PNR
		if ('Personal Identity Number' in i.samples[0].udf ) : 
			PNR = i.samples[0].udf['Personal Identity Number']
			match = re.search(r'^[0-9]{8}-[0-9a-zA-Z]{4}$', PNR)
			if not match : 
				print "Personal Identity Number must match YYYYMMDD-XXXX. Please check sample ", i.samples[0].name 
		#check analysis_field dictionary
		for k,v in analysis_fields.items() : 
			if (i.samples[0].udf['Analysis'] == k ): 
				for item in v : 
					if ( item not in i.samples[0].udf ) : 
						print "Check sample " , i.samples[0].name , " Missing info for either ", v
						sys.exit(255)
		#check read count
		if ('Desired read count' not in i.samples[0].udf ): 
			print i.samples[0].name , " must have value for Desired read count"
			sys.exit(255)
				
if __name__=='__main__':
	main()

