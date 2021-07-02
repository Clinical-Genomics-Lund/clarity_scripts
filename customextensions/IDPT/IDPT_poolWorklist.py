"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import glsapiutil
import xml.dom.minidom

def read_pool_data(process):
	pools = {}
	plates = {}

	for input, output in process.input_output_maps:
                if output['output-type'] == 'Analyte':
                        poolname = output["uri"].name
                        platename = input["uri"].location[0].name

                        if platename not in plates:
                                plates[platename] = len(plates) + 1

                        if poolname in pools:
                                pools[poolname] = pools[poolname] + [input["uri"]]
                        else:
                                pools[poolname] = [input["uri"]]

        if len(pools) > 24:
                sys.exit("Too many pools. Max 24.")
        if len(plates) > 3:
                sys.exit("Too many plates. Max 3.")

	return pools, plates

def construct_worklist(pools, plates):
        worklist = []
        orderedPools = []
        p = 1

        for pool in pools:
		# Get the pool number in the form 001, 002 etc.
                pnr = '0'*(3 - len(str(p))) + str(p)
		# Pools get appended in the order they are numbered
                orderedPools.append(pool)

                for sample in pools[pool]:
                        platenr = plates[sample.location[0].name]
                        sampleName = sample.name
                        limsID = sample.id
                        well = ''.join(sample.location[1].split(':'))

                        worklist.append('%s,%s,SamplePlate[00%d],%s,Pool[%s],A1,5\n' % (sampleName, limsID, platenr, well, pnr))
                p += 1

	return worklist, orderedPools

def order_worklist(worklist):
	wellorder = {'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8}
        platesList = {'1':[0]*len(worklist),'2':[0]*len(worklist),'3':[0]*len(worklist)}

	for line in worklist:
        	fields = line.split(',')
        	platenr = fields[2][-2]	# Get the plate number

        	try:
			# Get row letter and convert to a number. Get column number, for each column over 1 adds 8 samples. Minus one to get indexed from 0.
                	pos = wellorder[fields[3][0]] + (int(fields[3][1:]) - 1)*8 - 1
        	except:
                	sys.exit("Samples must be placed in a 96 well plate.")
        	platesList[platenr][pos] = line	

	return platesList

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

	pools, plates = read_pool_data(process)

	worklist, orderedPools = construct_worklist(pools, plates)

	platesList = order_worklist(worklist)

	# Write worklist to file
	with open((args[ "outfile" ] + '-pool-worklist.csv'), 'w') as outfile:
		outfile.write('Sample Name,Lims ID,source label,source well,dest label,dest well,volume\n')
		for i in ['1','2','3']:
			for line in platesList[i]:
				if line != 0:
					outfile.write(line)

	# Set the plate and pool order
	orderedPlates = ['','','']

	for plate in plates:
		orderedPlates[plates[plate] - 1] = plate

	process.udf['Plate order'] = ', '.join(orderedPlates)
	process.udf['Pool order'] = ', '.join(orderedPools)
	process.put()	

	print "Done"

if __name__=='__main__':
	main()

