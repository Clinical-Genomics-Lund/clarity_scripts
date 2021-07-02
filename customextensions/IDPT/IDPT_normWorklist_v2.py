"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import *
import sys
import getopt
import glsapiutil
import xml.dom.minidom
import xlsxwriter
import re

def visualization(f_out, sample) :
	global xrow
	global cell_format_2dec

	lcol = 0
	f_out.write_string(xrow, lcol, sample['sampleName'])
	lcol += 1
	f_out.write_string(xrow, lcol, sample['limsID'])
	lcol += 1
	try:
		f_out.write_number(xrow, lcol, sample['concentration'], cell_format_2dec)
	except:
		f_out.write_number(xrow, lcol, sample['concentration'])
	lcol += 1
	if sample['inWell'] == '11':
		f_out.write_string(xrow, lcol, '1:1')
	else:
		f_out.write_string(xrow, lcol, sample['inWell'])
	lcol += 1
	f_out.write_string(xrow, lcol, sample['outWell'])
	lcol += 1
	f_out.write_number(xrow, lcol, sample['sampleVolume'], cell_format_2dec)
	lcol += 1
	f_out.write_number(xrow, lcol, sample['waterVolume'], cell_format_2dec)
	lcol += 1

	xrow += 1

def calculate_volume(sampleConc, totalVolume):
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

def normalize_samples(process):
	global targetVolume
	targetVolume = 30

	rowTrans = {'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8}

        samples = ['']*96
	plateOrder = []
	plateAlias = {}
	tubeOrder = []

        for input, output in process.input_output_maps:
                if output['output-generation-type'] == 'PerInput':
			sample = {}

                	sample['sampleName'] = output['uri'].samples[0].name
	                sample['limsID'] = output['uri'].samples[0].id
			sample['inContainerType'] = input['uri'].location[0].type.name
			sample['inWell'] = ''.join( input['uri'].location[1].split(':') )
        	        sample['outWell'] = output['uri'].location[1].split(':')
			
			pos = rowTrans[ sample['outWell'][0] ] + ( int( sample['outWell'][1] ) - 1 )*8
			row = rowTrans[ sample['outWell'][0] ]
			sample['outWell'] = ''.join( sample['outWell'] )

			# Calculate volumes
			try:
				sample['concentration'] = output['uri'].samples[0].udf['Sample concentration (ng/ul)']
			except:
				sample['concentration'] = 'No measurement'

			try:
				sample['sampleVolume'] = process.udf['Take fixed volume']

			except:
				if "NegativeControl" in sample['sampleName']:
					sample['sampleVolume'] = 5

				elif sample['concentration'] != 'No measurement':
					sample['sampleVolume'] = calculate_volume( sample['concentration'], targetVolume )

					if sample['sampleVolume'] < 2:
						print("Error: Sample volume too small")
						sys.exit(255)

				else:
					print("Error: All samples must have a concentration at submitted sample level.")
					sys.exit(255)

			sample['waterVolume'] = targetVolume - sample['sampleVolume']

			# If normalization with Tecan, Order plates and tubes
			if process.udf['Method'] != 'Manuell':
				if sample['inContainerType'] == 'Tube':
					if len(tubeOrder) == 32:
						print('Fail: too many samples in tubes, max 32 tubes.')
						sys.exit(255)

					tubeOrder.append(sample['sampleName'])
					sample['inWell'] = 'A1'

					if len(tubeOrder) < 10:
						sample['containerStr'] = 'G1_5_ml_Micro_Tube[00%d]' % len(tubeOrder)

					else:
						sample['containerStr'] = 'G1_5_ml_Micro_Tube[0%d]' % len(tubeOrder)

				elif sample['inContainerType'] == '96 well plate':
					try:
						inContainerAlias = input['uri'].samples[0].udf[ 'Sample comments' ]

						if len(inContainerAlias) > 10:
							inContainerAlias = ''

					except:
						inContainerAlias = ''

					inContainerName = input['uri'].location[0].name

					if inContainerName not in plateOrder:
						plateOrder.append(inContainerName)
						plateAlias[inContainerName] = inContainerAlias

						if len(plateOrder) > 1:
							print('Fail: too many plates, max 1 plate.')
							sys.exit(255)

					elif plateAlias[inContainerName] == '' and inContainerAlias != '':
						plateAlias[inContainerName] = inContainerAlias

					sample['containerStr'] = 'SamplePlate[00%d]' % ( plateOrder.index(inContainerName) + 1 )

				else:
					print('Fail: Not an accepted container. Tecan can only handle plates and tubes. Change containers or normalize manually.')
					sys.exit(255)

				sample['waterTubeStr'] = 'G1_5ml_Eppendorf[00%d]' % ( ((row - 1) % 2) + 1 )

			# Save sample in position in output container
			samples[ pos - 1 ] = sample

	plates = []

	for plate in plateOrder:
		if plateAlias[plate] != '':
			plates.append( plate + '_' + plateAlias[plate] )
		else:
			plates.append( plate )

	return samples, plates, tubeOrder

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

	samples, plateOrder, tubeOrder = normalize_samples(process)

	if process.udf['Method'] == 'Manuell':
		f_outfile = xlsxwriter.Workbook(args[ "outfile" ] + '.xlsx')

		global cell_format_2dec
		global xrow

		cell_format_2dec = f_outfile.add_format()
		cell_format_2dec.set_num_format('0.00')

		f_outsheet = f_outfile.add_worksheet()

		columns = (20, 10, 20, 10, 10, 11, 23)

		for i in range(len(columns)):
			f_outsheet.set_column(i, i, columns[i])

		xrow = 0
		lcol = 0
		for i in ['LabID', 'LimsID', 'Concentration (ng/ul)', 'From Well', 'To Well', 'Sample (ul)', 'Nuclease Free Water (ul)']:
			f_outsheet.write(xrow, lcol, i)
			lcol += 1
		xrow += 1

		for sample in samples:
			if sample != '':
				visualization(f_outsheet, sample)

		f_outfile.close()

	else:
#		process.udf['Plate order'] = ', '.join(plateOrder)
		process.udf['Tube order'] = ', '.join(tubeOrder)
		process.udf['Method: Pooling'] = process.udf['Method']
		process.udf['Method: Set-up'] = process.udf['Method']
		process.udf['Second Bio-Rad Thermal Cycler'] = "James Bond (CT032030)"
		process.put()

		with open( (args[ "outfile" ] + '-normWorklist.csv'), 'w' ) as outfile:
			outfile.write('Sample Name,Lims ID,source label,source well,dest label,dest well,volume,liquid class\n')

			for sample in samples:
				if sample != '':
					outfile.write( '%s,%s,%s,%s,DestPlate,%s,%.2f,CMD NexteraFlex cDNA Zmax Single\n' % ( sample['sampleName'], sample['limsID'], sample['containerStr'], sample['inWell'], sample['outWell'], sample['sampleVolume'] ) )

			for sample in samples:
				if sample != '':
					outfile.write( '%s,%s,%s,A1,DestPlate,%s,%.2f,Water Free Single\n' % ( sample['sampleName'], sample['limsID'], sample['waterTubeStr'], sample['outWell'], sample['waterVolume'] ) )

	print "Done"

if __name__=='__main__':
	main()

