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
	process = Process(lims,id= args[ "stepID" ])

	savedOutput = []
	savedInput = []
	allInput = []

	for inArt, outArt in process.input_output_maps :
		if outArt['output-generation-type']=='PerInput':
			if 'NegativeControl' in outArt['uri'].name:
				outArt['uri'].samples[0].udf['Desired read count'] = 400000
				outArt['uri'].samples[0].udf['Analysis'] = 'Sars-CoV-2 IDPT'
				outArt['uri'].samples[0].udf['Department'] = 'Klinisk Mikrobiologi'
				outArt['uri'].samples[0].udf['Sequencing runs'] = 0
				if 'Micro' in outArt['uri'].name:
					outArt['uri'].samples[0].udf['Classification'] = 'Extern Kvalitetskontroll'
				else:
					outArt['uri'].samples[0].udf['Classification'] = 'Intern Kvalitetskontroll'
				outArt['uri'].samples[0].udf['Nucleotide Type'] = 'H2O'
				outArt['uri'].samples[0].put()

			print outArt['uri'].samples[0].udf['Desired read count']


if __name__=='__main__':
	main()

