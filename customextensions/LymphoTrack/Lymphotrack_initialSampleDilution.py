"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import re
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
			args[ "outFile" ] = p
        BASEURI = args["BASEURI"].split('api')[0]

        lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
        lims.check_version()
        process = Process(lims,id= args[ "stepID" ])
	
	targetConc = 10
	targetVolume1 = 10
	targetVolume2 = 30
	xrow = 0
	lcol = 0

	xlsxOutFile = xlsxwriter.Workbook(args[ "outFile" ] + '.xlsx')
	outSheet = xlsxOutFile.add_worksheet()

	columns = (20, 20, 5, 20, 20, 20, 20, 20)
	for i in range(len(columns)):
		outSheet.set_column(i, i, columns[i])
	
	for i in ['Sample Name', 'Container LIMS ID', 'Well', 'Concentration ng/ul', 
		  'Sample Volume %s ul' % targetVolume1, 'Buffert Volume %s ul' % targetVolume1,
		  'Sample Volume %s ul' % targetVolume2, 'Buffert Volume %s ul' % targetVolume2]:
		outSheet.write(xrow, lcol, i)
		lcol += 1
	xrow += 1
	
        for inArt, output in process.input_output_maps :
		if output['output-generation-type'] == 'PerInput':
			sampleName = output['uri'].samples[0].name
			conc = int(inArt['uri'].samples[0].udf['Sample concentration (ng/ul)'])
			well = output['uri'].location[1]
			container = output['uri'].location[0].name

			sampleVolume1 = targetConc*targetVolume1/conc
			sampleVolume2 = targetConc*targetVolume2/conc

			if sampleVolume1 > targetVolume1:
				sampleVolume1 = targetVolume1
			if sampleVolume2 > targetVolume2:
				sampleVolume2 = targetVolume2

			bufferVolume1 = targetVolume1 - sampleVolume1
			bufferVolume2 = targetVolume2 - sampleVolume2

			lcol = 0
			for i in [sampleName, container, well, conc, sampleVolume1, bufferVolume1, sampleVolume2, bufferVolume2]:
				outSheet.write(xrow, lcol, i)
				lcol += 1
			xrow += 1

	xlsxOutFile.close()

if __name__=='__main__':
        main()

