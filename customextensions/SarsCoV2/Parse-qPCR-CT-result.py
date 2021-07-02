"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import datetime
import re
import glsfileutil
import csv
import glsapiutil

def parse_file(filename):
	results = {}

	with open(filename, 'r') as file:
		readlines = False

		for line in file:
			if readlines:
				try:
					line = line.split('\t')
	
					while line[0] in results:
						line[0] = line[0] + '-'

					results[line[0]] = line[2]

				except:
					pass

			elif '[Results]' in line:
				readlines = True
				next(file)

	return results

def get_results(process) :

        #get output file
        for output in process.all_outputs() :

                if output.name == "Result file" :
                        try:
                                fid = output.id
			except:
                                print ('No result file found')
                                sys.exit(255)
                        break

        return fid

def main():
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:x:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-s':
			args[ "stepID" ] = p
		elif o == '-x':
			args[ "stepURI" ] = p

	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()

	process = Process(lims,id= args[ "stepID" ])
	step = Step(lims,id= args[ "stepID" ])

	fileID = get_results(process)

        api = glsapiutil.glsapiutil2()
        api.setURI( args[ "stepURI" ] )
        api.setup( args["USERNAME"], args["PASSWORD"])

        global FH
        FH = glsfileutil.fileHelper()
        FH.setAPIHandler( api )
        FH.setAPIAuthTokens( args["USERNAME"], args["PASSWORD"] )

        newName = str( fileID ) + ".txt"
        FH.getFile( fileID, newName )
        content = open( newName, "r")
        content.close

	resultsCT = parse_file(newName)
	
	process.udf['NTC'] = '%s, %s, %s, %s' % (resultsCT['Neg'], resultsCT['Neg-'], resultsCT['Neg--'], resultsCT['Neg---'])
        process.udf['PTC'] = '%s, %s' % (resultsCT['Pos'], resultsCT['Pos-'])
	process.put()

	for inart, outart in process.input_output_maps:

		if outart[ 'output-generation-type' ] == 'PerInput':
			if outart['uri'].name in resultsCT:
				outart['uri'].udf['CT'] = resultsCT[ outart['uri'].name ]
				outart['uri'].put()
			else:
				print "Sample not in resultfile."
				sys.exit(255)


	print "Done"

if __name__=='__main__':
	main()

