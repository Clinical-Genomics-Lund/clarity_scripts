"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt

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
	process = Process(lims,id= args[ "stepID" ])

	barcodes = {process.udf[ 'Plate 1' ]:'1',
			process.udf[ 'Plate 2' ]:'2',
			process.udf[ 'Plate 3' ]:'3',
			process.udf[ 'Plate 4' ]:'4'}

	posMap = {}
	with open('/opt/gls/clarity/customextensions/SarsCoV2/Sars-CoV-2_qPCR-map.csv', 'r') as mapfile:
		for line in mapfile:
			line = line.strip().split(':')
			posMap[line[0]] = line[1]

	qPCRstring = ',SARS-2-Screening,UNKNOWN,FAM,None,'

	for input in process.all_inputs(unique = True):
		plate = input.location[0].name
		well = ''.join(input.location[1].split(':'))

		if plate in barcodes:
			platenumber = barcodes[ plate ]
			plateWell = platenumber + '_' + well
			pos = ','.join(posMap[ plateWell ].split(',')[0:2])
			samplename = input.samples[0].name

			posMap[ plateWell ] = pos + ',' + samplename + qPCRstring
		else:
			sys.exit("Barcode not found. The order of plates must be given by entering the barcodes in the step fields.")

	with open((args[ "outfile" ] + '-plate-setup.csv'), 'w') as outfile:
		outfile.write('[Sample Setup],,,,,,,\nWell,Well Position,Sample Name,Target Name,Task,Reporter,Quencher,Comments\n')

		for key in posMap:
			outfile.write( posMap[ key ] + '\n')

	print "Done"

if __name__=='__main__':
	main()

