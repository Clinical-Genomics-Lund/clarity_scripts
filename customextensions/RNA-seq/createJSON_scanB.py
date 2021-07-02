"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
from genologics.entities import SampleHistory , Step, StepReagentLots
import os 
import sys
import getopt
import pprint 
import json 
import random 
import subprocess

def get_library_info(scanB, json_content, libraryInfo, artifact ) :

	#json_content[scanB]['Library'] = {}

	json_content[scanB]['Library']['Date'] = libraryInfo['date']
	json_content[scanB]['Library']['Protocol'] = 'CMD protocol'
	json_content[scanB]['Library']['Barcode'] = artifact.reagent_labels[0]
	json_content[scanB]['Library']['Plate name'] = artifact.location[0].name
	json_content[scanB]['Library']['Plate well'] = artifact.location[1]
	try: 
		json_content[scanB]['Library']['Qubit concentration (ng/ul)'] = float(libraryInfo['oUdfs']['Qubit concentration (ng/ul)'])
	except: 
		json_content[scanB]['Library']['Qubit concentration (ng/ul)'] = None

	try:
                json_content[scanB]['Library']['Library size'] = float(libraryInfo['oUdfs']['Region 1 Average Size - bp'])
        except:
                json_content[scanB]['Library']['Library size'] = None

	try: 
		nM = float(libraryInfo['oUdfs']['Qubit concentration (ng/ul)']) / (660.0 * float(libraryInfo['oUdfs']['Region 1 Average Size - bp'])) * 1000000 
		nM = "{:.2f}".format(nM)
		json_content[scanB]['Library']['Library molarity'] = float(nM) 
	except: 
		json_content[scanB]['Library']['Library molarity'] = None
	
	
	json_content[scanB]['Library']['Operator'] = 'CMD personnel'
	
        return json_content


def get_extraction_info(scanB, json_content, extractionInfo ) :
	
	mlist = ['RNA', 'DNA', 'FlowThrough'] 

	for item in mlist :
                json_content[scanB][item]['Qiacube date'] = extractionInfo['date']
		json_content[scanB][item]['Protocol'] = 'CMD protocol'
		json_content[scanB][item]['Qiacube position'] = extractionInfo['oWell'] 
		json_content[scanB][item]['Qiacube operator'] = 'CMD personnel'
		json_content[scanB][item]['Qiacube run number'] = extractionInfo['oContID']


		#Lot numbers
		try: 
			for reagent in extractionInfo['reagents'].reagent_lots : 
				if reagent.reagent_kit.id == '854' : 
					json_content[scanB][item]['Extraction kit'] = reagent.lot_number 
		except: 
			json_content[scanB][item]['Extraction kit'] = None 
	
	return json_content
	
def get_lysate_info(scanB, json_content, lysateInfo ) :

	#Complementary specimen info 
	try: 
		json_content[scanB]['Specimen']['Original quantity (mg)'] = float(lysateInfo['oUdfs']['Total quantity (mg)'])
	except: 
		json_content[scanB]['Specimen']['Original quantity (mg)'] = None 
	try:
		json_content[scanB]['Specimen']['Remaining quantity (mg)'] = float(lysateInfo['oUdfs']['Total quantity (mg)'] - lysateInfo['oUdfs']['Used quantity (mg)'])
	except : 
		json_content[scanB]['Specimen']['Remaining quantity (mg)'] = None

	#Lysate info 
	json_content[scanB]['Lysate']['Partition date'] = lysateInfo['date']
	json_content[scanB]['Lysate']['Lysate date'] = lysateInfo['date']
	try: 
		json_content[scanB]['Lysate']['Used quantity (mg)'] = float(lysateInfo['oUdfs']['Used quantity (mg)'])
	except: 
		json_content[scanB]['Lysate']['Used quantity (mg)'] = None 

	try:
		json_content[scanB]['Lysate']['Original volume (ul)'] = float(lysateInfo['oUdfs']['Lysis buffer (ul)'])
        except:
                json_content[scanB]['Lysate']['Original volume (ul)'] = None
		
	json_content[scanB]['Lysate']['Protocol'] = 'CMD protocol'

	#Lot numbers 
	try:
                for reagent in lysateInfo['reagents'].reagent_lots :
                        if reagent.reagent_kit.id == '852' :
                                json_content[scanB]['Lysate']['RLT_Plus'] = reagent.lot_number
        except :
                json_content[scanB]['Lysate']['RLT_Plus'] = None


	try:
		for reagent in lysateInfo['reagents'].reagent_lots :
                        if reagent.reagent_kit.id == '853' :
                                json_content[scanB]['Lysate']['QiaShredder'] = reagent.lot_number
        except:
                json_content[scanB]['Lysate']['QiaShredder'] = None

	return json_content


def get_specimen_info(sample) :
	json_content = {}
	
	submittedSampleFields = [
		'Arrival date',
		'Sampling date + time',
		'RNA later date + time',
		'Biopsy type',
		'Specimen type',
		'Laterality',
		'Number of delivered tubes',
		'Number of pieces',
		'PAD',
		'Sample comments',
		'Operator partition comment',
		'Other pathology note'
		]

	try:
                scanB = sample.udf['SCAN-B ID' ]
                json_content[scanB] = {}
	except:
                print "Can not continue without 'SCAN-B ID' or Sample Name"
                sys.exit(255)

	keyList = [ "Specimen" ,"Lysate", "DNA" , "RNA", "FlowThrough", "Library", "Pool"]
	for key in keyList :
		json_content[scanB][key] = {}

	json_content[scanB]['Specimen']['Sample Name'] = sample.name
	json_content[scanB]['Specimen']['Clarity ID'] = sample.id


	for field in submittedSampleFields :
                try:
                        json_content[scanB]['Specimen'][field] =  sample.udf[submittedSampleFields[field]]
                except:
                        json_content[scanB]['Specimen'][field] = None

	return  scanB , json_content
	

def main():
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
			args[ "processID" ] = p

	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()

	process = Process(lims, id=  args[ "processID" ] ) 
	inputs = process.all_inputs(unique=True)
	scanB_inputs = [] 
	for a in inputs : 
		if a.samples[0].udf['Analysis'] == "TruSeq Stranded mRNA - Expression - Breast" : 
			scanB_inputs.append(a)
	
	for artifact in scanB_inputs : 
		sampleID = artifact.samples[0].id
		sample = Sample(lims, id=sampleID) 

		#Get specimen info
		scanB, json_content = get_specimen_info(sample) 
	
		#Get history of artifact 
		out = artifact
		history_map = {}
	
		while  out.parent_process :
		
			for i, o in out.parent_process.input_output_maps:
				if o['limsid'] == out.id :
					inp = Artifact(lims,  id= i['limsid'] )
					step = Step(lims, id =  out.parent_process.id)
					
					history_map[out.id] = {'date': out.parent_process.date_run,
							       'id': out.parent_process.id,
							       'pUdfs' : out.parent_process.udf,
							       'instrument' : out.parent_process.instrument, 
							       'reagents' : step._reagent_lots, 
							       'inart': inp.id,
							       'iUdfs' : inp.udf,
							       'iWell' : inp.location[1],
							       'outart': out.id,
							       'oUdfs' : out.udf,
							       'oWell' : out.location[1],
							       'oContID' : out.container.id ,
							       'type': out.parent_process.type.id,
							       'name': out.parent_process.type.name}
					out = inp
				
		
		#pprint.pprint(history_map)

		for art in history_map.keys() : 
			if history_map[art]['type']  == '1004':
				#Lysate 
				json_content = get_lysate_info(scanB, json_content, history_map[art])

			if history_map[art]['type']  == '362':
				#Extraction 
				json_content = get_extraction_info(scanB, json_content, history_map[art])
				output_art = Artifact(lims, id =  history_map[art]['outart'])

				#Save original RNA conc
				try: 
					json_content[scanB]['RNA']['Concentration (ng/ul)'] = float(output_art.udf['Qubit concentration (ng/ul)'])
				except: 
					json_content[scanB]['RNA']['Concentration (ng/ul)'] = None

				#Save original DNA conc
				sample = output_art.samples[0]
				history = SampleHistory( sample, lims=sample.lims, input_artifact = output_art.id )
				dna_process = ""
				for processID in history.history[output_art.id] :
					if history.history[output_art.id][processID]['type'] == '314':
						if dna_process == "" :
							dna_process = history.history[output_art.id][processID]['id']
						else: 
							if history.history[output_art.id][processID]['id'] > dna_process :
								dna_process = history.history[output_art.id][processID]['id']
						
				dna_process = Process(lims, id=dna_process) 
				for i, o in dna_process.input_output_maps : 
					if i['limsid'] == output_art.id : 
						if o['output-generation-type'] == 'PerInput' : 
							try: 
								dna_out = Artifact(lims,id = o['limsid'])
								json_content[scanB]['DNA']['Concentration (ng/ul)'] = float(dna_out.udf['Qubit concentration (ng/ul)'])
							except:
								json_content[scanB]['DNA']['Concentration (ng/ul)'] = None
			

			if history_map[art]['type']  == '609':
				#Sample dilution (diluted sample goes to qubit and tapestation)
				#Get RIN
				output_art = Artifact(lims, id =  history_map[art]['outart'])
				sample = output_art.samples[0]
                                history = SampleHistory( sample, lims=sample.lims, input_artifact = output_art.id )
                                tape_process = ""
                                for processID in history.history[output_art.id] :
                                        if history.history[output_art.id][processID]['type'] == '570':
                                                if tape_process == "" :
                                                        tape_process = history.history[output_art.id][processID]['id']
                                                else:
                                                        if history.history[output_art.id][processID]['id'] > tape_process :
                                                                tape_process = history.history[output_art.id][processID]['id']

                                tape_process = Process(lims, id=tape_process)
                                for i, o in tape_process.input_output_maps :
                                        if i['limsid'] == output_art.id :
                                                if o['output-generation-type'] == 'PerInput' :
                                                        try:
                                                                tape_out = Artifact(lims,id = o['limsid'])
                                                                json_content[scanB]['RNA']['RIN'] = float(tape_out.udf['RIN'])
                                                        except:
                                                                json_content[scanB]['RNA']['RIN'] = None

			if history_map[art]['type']  == '566':
				#Library
				json_content = get_library_info(scanB, json_content, history_map[art], artifact)


		#Pool 
		try:
			json_content[scanB]['Pool']['Pool ID' ] = artifact.udf['PoolID']
		except:
			json_content[scanB]['Pool']['Pool ID' ] = None
		
		poolProcess = Process(lims, id= artifact.udf['PoolID'] ) 
		json_content[scanB]['Pool']['Date' ] = poolProcess.date_run
		json_content[scanB]['Pool']['Operator' ] = 'CMD personnel' 

		#Save json file 
		outputFile = scanB + "_" +  str(random.randrange(1000000,9999999)) + ".json"
		path = "/all/" + outputFile
		with open(path, 'w') as outfile:
			json.dump( json_content, outfile, indent=6)
		
		#Save on Lennart
		server = "petter@10.0.224.63"
		dir_path = "/data/bnf/proj/scanb_clarity/"
		result = subprocess.call(["scp", path, "%s:%s" % (server, dir_path)])

		os.system("rm "+path)
				
if __name__=='__main__':
	main()

