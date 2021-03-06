"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import *
import sys
import getopt
import datetime
import csv
import glsapiutil
import glsfileutil
import re

def convert_well_from_file_to_clarity(well) :
	try:
		well = well.replace("A", "1:")
	except:
		print("Well column not corrrectly formatted")
	return well

def convert_well_format(well) : 
	try: 
		well = well.replace(":", "") 
	except: 
		print("Well column not corrrectly formatted") 
	return well

#fill values to clarity
def copy_to_clarity(process ,instrument, data, st1, st2 ):
        try:
		process.udf['Standard 1 (RFU)'] = float(st1)
		process.udf['Standard 2 (RFU)'] = float(st2)
		process.put()
	except Exception, e:
		print e

        # Sample UDF and data map
	if process.type.name in [ 'NIPT - Initial Qubit High Sensitivity v.2', 
				  'Library Quantification - Qubit - DNA v.1', 
				  'Initial sample quantification - Qubit v.2', 
				  'Library quantification - Qubit v.2', 
				  'Initial Sample Quantification - Qubit - DNA v.1'] :
		map = [('Original Sample Conc.', 'Qubit concentration (ng/ul)')]

	elif process.type.name == 'NIPT - Purification and Library Quantification - Qubit High Sensitivity v.1' :
		map = [('Original Sample Conc.', 'Qubit concentration 1 (ng/ul)')]

	elif process.type.name in [ 'Library Quantification PicoGreen v.2', 'Initial Qubit HS measurement v.1', 'Bio-Rad PCR v.1'] :
		map = [('Original Sample Conc.', 'Concentration (ng/ul)')]
	else:
		print "Process name does not match"
		sys.exit(255)

	for out in process.all_outputs():
		found_flag = False

		for k, v in data.items():
			if out.location[1] != None : 
				if instrument == "Platereader" :
					well = convert_well_format(out.location[1])
					if k == well:
						try: 
							found_flag = True
							for item in map:
								out.udf[item[1]] = float(v )
						except Exception as e :
							print e
							sys.exit(255)
				elif instrument == "QubitFlex":
					limsID = v['Sample ID'].split("_")[0]
					well = convert_well_from_file_to_clarity(v['Well'])
					#match limsID and well
					if limsID == out.samples[0].id and well == out.location[1]:
						found_flag = True
						for item in map:
							if v[item[0]] != 'NA':
								out.udf[item[1]] = float( v[item[0]] )
								print float( v[item[0]] )
							else:
								print("Sample {} in well {} missing.".format(v['Sample ID'], v['Well']))
								sys.exit(255)

		if found_flag:
			out.put()
	
# Parse file content
def get_data(instrument , content):
	
	data = dict()
	headers = dict()
	pf = csv.reader(content.readlines(), delimiter=',')

	st1 = ""
	st2 = ""

	for row in pf:
		if instrument == "Platereader" :
			try:
				if len(row) == 5 and row[0] != 'well':
					if row[1] != "" :
						well = row[1]

						#Remove redundant zeros in well index
						well = well.split('_')
						well = list(well[1])

						if re.match('[1-9]', well[2]):
							well = well[0]+well[2]+well[3]
						else:
							well = well[0]+well[3]

						conc = row[4]
						conc = float( conc )
						data[well] = conc
						if well == "B1" and row[2] == 1:
							st1 = conc
						else:
							st1 = "0"

						if well == "H1" and row[2] == 1:
							st2 = conc
						else:
							st2 = "0"

			except Exception as e : 
				print e
				sys.exit(255)

		if instrument == "QubitFlex" : 
			# Header line
			if 'Sample ID' in row:
				for item in row :
					#header title, index of the header title
					headers[item] = row.index(item)
			else:
				if (st1 == "" and st2 == "") :
					try: 
						st1 = row[headers['Std 1 RFU']]
						st2 = row[headers['Std 2 RFU']]
					except :
						print "Wrong format" 
						sys.exit(255)
				sample_data = dict()
				for k, v in headers.items():
					sample_data[k] = row[v]
					data.update({row[headers['Sample ID']]: sample_data})

	return data, st1, st2


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
	selected_container = step.placements.get_selected_containers()
	instrument = ""
	if selected_container[0].type.name == "8-striptubes":
		instrument = "QubitFlex"
	if selected_container[0].type.name == "96 well plate":
		instrument = "Platereader"

	fileID = get_results(process)

	#download result file	
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
	
	if instrument == "Platereader" :
		#content = lims.get_file_contents(id=fileID, uri=newName)
		#parse the output 
		data, st1, st2 = get_data(instrument, content)
		copy_to_clarity(process, instrument, data, st1, st2)

	elif instrument == "QubitFlex" : 
		#parse the output
		data, st1, st2 = get_data(instrument, content)
		copy_to_clarity(process, instrument, data, st1, st2)

	print "Done :)" 
				
if __name__=='__main__':
	main()

