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
	
	analysis_fields = { 
		'TruSeq DNA PCR free - WGS - constitutional - family' : ['FamilyID' ,  'Pedigree' , 'Sex' , 'Sample Type' ],
		'TruSeq DNA PCR free - WGS - somatic - paired' : ['Sex' , 'Sample Type' , 'Paired Sample Name'], 
		'TruSeq DNA PCR free - WGS - somatic - unpaired' : ['Sex' , 'Sample Type'] 
		}

	family = {}
	for input, output in process.input_output_maps : 
		if output['output-generation-type'] == 'PerInput':

			#stop invalid sample names
			characters = r"_/\ ?.%*"		
			if ( any(elem in input['uri'].name for elem in characters) == True) : 
				print "Please check sample " , input['uri'].name , ".The folowing charachters are not allowed _/\ ?.%*"
				sys.exit(255)
			#check PNR
			if ('Personal Identity Number' in input['uri'].samples[0].udf ) : 
				PNR = input['uri'].samples[0].udf['Personal Identity Number']
				match = re.search(r'^[0-9]{8}-[0-9a-zA-Z]{4}$', PNR)
				if not match : 
					print "Personal Identity Number must match YYYYMMDD-XXXX. Please check sample ", input['uri'].samples[0].name 
			#check single WGS samples
			if (input['uri'].samples[0].udf['Analysis'] == 'TruSeq DNA PCR free - WGS - constitutional - single' ) :
				if ('Sex' not in input['uri'].samples[0].udf ) : 
					print "sample " , input['uri'].samples[0].name , "must have value for sex" 
					sys.exit(255)
				if ('Diagnosis' not in input['uri'].samples[0].udf and 'Gene list' not in input['uri'].samples[0].udf ) :
					print "sample " , input['uri'].samples[0].name , "must have value for diagnosis och gene list"
					sys.exit(255)
			#check analysis_field dictionary
			for k,v in analysis_fields.items() : 
				if (input['uri'].samples[0].udf['Analysis'] == k ): 
					for item in v : 
						if ( item not in input['uri'].samples[0].udf ) : 
							print "Check sample " , input['uri'].samples[0].name , " Missing info for either ", v
							sys.exit(255)
			#check read count
			if ('Desired read count' not in input['uri'].samples[0].udf ): 
				print input['uri'].samples[0].name , " must have value for Desired read count"
				sys.exit(255)

			output['uri'].udf['Skip Quantification'] = True
			output['uri'].put()
				
if __name__=='__main__':
	main()

