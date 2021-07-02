"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import glsapiutil
import xml.dom.minidom

def normalizeconc(sampleConc):
	totalVolume = 30
	minVolume = 2
	loadingMassMin = 100
	loadingMassMax = 500

	targetMass = (loadingMassMax - loadingMassMin)/2 + loadingMassMin
	concMin = loadingMassMin/totalVolume
	concMax = loadingMassMax/minVolume

        if sampleConc < concMin:
        	sampleVolume = totalVolume

        elif sampleConc > concMax:
                sampleVolume = minVolume

        else:
		sampleTargetMass = targetMass
		sampleVolume = sampleTargetMass/sampleConc

		while sampleVolume < minVolume or sampleVolume > totalVolume:
                        if sampleVolume < minVolume:
				sampleTargetMass = sampleTargetMass + 10

                        elif sampleVolume > totalVolume:
				sampleTargetMass = sampleTargetMass - 10

			sampleVolume = sampleTargetMass/sampleConc

			if sampleTargetMass <= loadingMassMin or sampleTargetMass >= loadingMassMax:
				break

	return sampleVolume

def construct_worklist(process):
        worklist = []
	waterWorklist = []
	targetVolume = 30
	plateOrder = {}
	tubeOrder = {}

	try:
		fixedVolume = process.udf['Take fixed volume']
	except:
		fixedVolume = False

        for input, output in process.input_output_maps:
                if output['output-generation-type'] == 'PerInput':
                	sampleName = output['uri'].samples[0].name
	                limsID = output['uri'].samples[0].id
        	        well = ''.join(output['uri'].location[1].split(':'))

			try:
				conc = output['uri'].samples[0].udf['Sample concentration (ng/ul)']
			except:
				sys.exit("Error: All samples must have a concentration at submitted sample level.")

			if fixedVolume:
				normVolume = fixedVolume
			elif "NegativeControl" in sampleName:
				normVolume = 5
			else:
				normVolume = normalizeconc(conc)

			waterVolume = targetVolume - normVolume

			rowTrans = {'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8}
			row = (rowTrans[list(well)[0]]-1)
			waterTube = (row % 2) + 1

			if normVolume >= 2:
				worklist.append('%s,%s,SamplePlate,%s,DestPlate,%s,%.2f,CMD NexteraFlex cDNA Zmax Single\n' % (sampleName, limsID, well, well, normVolume))
			else:
				sys.exit("Error: Sample volume too small")

			if waterVolume > 0:
				waterWorklist.append('%s,%s,G1_5ml_Eppendorf[00%d],A1,DestPlate,%s,%.2f,Water Free Single\n' % (sampleName, limsID, waterTube, well, waterVolume))

	return worklist, waterWorklist

def order_worklist(worklist):
	wellorder = {'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8}
	orderedList = ['']*96

	for line in worklist:
        	fields = line.split(',')

        	try:
			# Get row letter and convert to a number. Get column number, for each column over 1 adds 8 samples. Minus one to get indexed from 0.
                	pos = wellorder[fields[5][0]] + (int(fields[5][1:]) - 1)*8 - 1
        	except:
                	sys.exit("Samples must be placed in a 96 well plate.")

		print(pos)
        	orderedList[pos] = line

	return orderedList

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

	worklist, waterWorklist = construct_worklist(process)

	orderedList = order_worklist(worklist)
	orderedWater = order_worklist(waterWorklist)

	# Write worklist to file
	with open((args[ "outfile" ] + '-normWorklist.csv'), 'w') as outfile:
		outfile.write('Sample Name,Lims ID,source label,source well,dest label,dest well,volume,liquid class\n')
		for line in orderedList:
			if line != '':
				outfile.write(line)
				print line

		for line in orderedWater:
			if line != '':
				outfile.write(line)
				print line

	print "Done"

if __name__=='__main__':
	main()

