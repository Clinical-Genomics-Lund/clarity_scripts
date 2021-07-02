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

	worklist = []
	plates = []

	for output in process.all_outputs():
		if output.name != 'Index worklist':
			if not output.location[0] in plates:
				plates.append(output.location[0])

			well = ''.join(output.location[1].split(':'))
			index = output.reagent_labels[0].split(' ')
			indexwell = index[0][-1] + index[0][0:-1]

			worklist.append('Index Plate[00#],%s,PCR Plate,%s,10\n' % (indexwell, well))

	if len(plates) > 1:
		sys.exit("Only one 96 well plate can be indexed at a time.")

	wellorder = {'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8}
	ordered_worklist = [0]*96

	for line in worklist:
		fields = line.split(',')
		pos = wellorder[fields[3][0]] + (int(fields[3][1:]) - 1)*8 - 1
		ordered_worklist[pos] = line

	worklist = []
	indexplate = '1'
	for line in ordered_worklist:
		if line != 0:
			line = line.replace('#', indexplate)
			worklist.append(line)

			indexwell = line.split(',')[1]
			if indexwell == 'H12':
				indexplate = '2'

	with open((args[ "outfile" ] + '-index-worklist.csv'), 'w') as outfile:
		outfile.write('source label,source well,dest label,dest well,volume\n')
		for line in worklist:
			outfile.write(line)

	print "Done"

if __name__=='__main__':
	main()

