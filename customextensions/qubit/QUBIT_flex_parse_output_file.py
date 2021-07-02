"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import *
import sys
import getopt
import datetime
import csv

def convert_well_from_file_to_clarity(well) : 
	try: 
		well = well.replace("A", "1:") 
	except: 
		print("Well column not corrrectly formatted") 
	return well

#fill values to clarity
def copy_to_clarity(process , data, st1, st2):
	try: 
		process.udf['Standard 1 (RFU)'] = float(st1)
		process.udf['Standard 2 (RFU)'] = float(st2)
		process.put()
	except Exception, e:
		print e
	
	# Sample UDF and data map
	if process.type.name in [ 'NIPT - Initial Qubit High Sensitivity v.2', 'Library Quantification - Qubit - DNA v.1', 'Initial sample quantification - Qubit v.2', 'Library quantification - Qubit v.2', 'Initial Sample Quantification - Qubit - DNA v.1'] : 
		map = [('Original Sample Conc.', 'Qubit concentration (ng/ul)')]
	elif process.type.name == 'NIPT - Purification and Library Quantification - Qubit High Sensitivity v.1' : 
		map = [('Original Sample Conc.', 'Qubit concentration 1 (ng/ul)')]
	elif process.type.name in [ 'Library Quantification PicoGreen v.2', 'Initial Qubit HS measurement v.1'] :
                map = [('Original Sample Conc.', 'Concentration (ng/ul)')]
	else: 
		print "Process name does not match" 
		sys.exit(255)

	for out in process.all_outputs():
		found_flag = False

		for k, v in data.items():
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
					#set_field(out)
				else:
					print ('No record of sample {} in well {}.'.format(out.name[0], out.location[1]))

# Parse file content
def get_data(content):
	data = dict()
	headers = dict()
	pf = csv.reader(content.splitlines(), delimiter=',')
	st1 = ""
	st2 = ""
	for row in pf:
		try:
			# Header line
			if 'Sample ID' in row:
				for item in row:
					#header title, index of the header title
					headers[item] = row.index(item)
			else:
				if (st1 == "" and st2 == "") :
					st1 = row[headers['Std 1 RFU']]
					st2 = row[headers['Std 2 RFU']]

				sample_data = dict()
				for k, v in headers.items():
					sample_data[k] = row[v]
					data.update({row[headers['Sample ID']]: sample_data})
		except:
			print('File in bad format')

	return data, st1, st2

def get_qubitFlex_results(process) : 

	#get output file
	for output in process.all_outputs() :
		if output.name == "Result file" :
			try:
				fid = output.files[0].id
			except:
				print ('No result file found')
				sys.exit(255)
			break

	return fid

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
	fileID = get_qubitFlex_results(process)
	content = lims.get_file_contents(id=fileID)
	#parse the output 
	data, st1, st2 = get_data(content)
	copy_to_clarity(process, data, st1, st2)
	
				
if __name__=='__main__':
	main()

