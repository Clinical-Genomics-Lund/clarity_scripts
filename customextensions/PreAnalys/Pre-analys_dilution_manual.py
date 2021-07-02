"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import xlsxwriter

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

	f_outfile = xlsxwriter.Workbook(args[ "outfile" ] + '.xlsx')
	f_outsheet = f_outfile.add_worksheet()

	cell_format_2dec = f_outfile.add_format()
	cell_format_2dec.set_num_format('0.00')

	columns = (30, 30, 20, 20)
	for i in range(len(columns)):
		f_outsheet.set_column(i, i, columns[i])

	xrow = 0
	targetload = float(process.udf[ 'Total load (ng)' ])
        totalvolume = float(process.udf[ 'Total volume (ul)' ])
	
	lcol = 0
	for i in ['RS LimsID', 'Clariy LimsID', 'Sample volume (ul)', 'Buffer volume (ul)']:
		f_outsheet.write(xrow, lcol, i)
		lcol += 1
	xrow += 1

	for input in process.all_inputs(unique = True):
		try:
			conc = float(input.samples[0].udf['Sample concentration (ng/ul)'])
			samplevolume = targetload/conc
			buffervolume = totalvolume - samplevolume

			lcol = 0
			f_outsheet.write(xrow, lcol, input.name)
			lcol += 1
                        f_outsheet.write(xrow, lcol, input.samples[0].id)
			lcol += 1
                        f_outsheet.write(xrow, lcol, samplevolume, cell_format_2dec)
			lcol += 1
                        f_outsheet.write(xrow, lcol, buffervolume, cell_format_2dec)
			xrow += 1
		except:
			print "Qubit concentration not found. All samples must have a qubit concentration at sumbitted sample level."
			sys.exit(255)

	f_outfile.close()

if __name__=='__main__':
	main()


