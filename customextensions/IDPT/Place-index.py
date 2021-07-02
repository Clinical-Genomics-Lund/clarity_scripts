"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import glsapiutil
import xml.dom.minidom

def main():
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:s:l:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-s':
			args[ "stepID" ] = p
		elif o == '-l':
			args[ "outfile" ] = p

	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()
	process = Process(lims, id= args[ "stepID" ])

	indexlist = [0]*96
	i = 0
	with open('/opt/gls/clarity/customextensions/COMMON/indexSetA.txt', 'r') as indexfile:
		for line in indexfile:
			if i < 96:
				indexlist[i] = line.strip()
				i += 1

	i = 0
	for output in process.all_outputs():
		if output.name != 'Index worklist':
			print output.reagent_labels
			well = ''.join(output.location[1].split(':'))
			output.reagent_labels = indexlist[i]
			print output.reagent_labels
			output.put()
			print output.reagent_labels
			i += 1

if __name__=='__main__':
	main()

