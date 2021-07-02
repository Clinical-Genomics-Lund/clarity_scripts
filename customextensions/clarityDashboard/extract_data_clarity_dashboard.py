"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
#from genologics.entities import SampleHistory
import sys
import os
import getopt
import csv
from datetime import datetime

def main():
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:s:u:p:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	print "script started " , datetime.now()
	lims.check_version()

	########################################
	#Get all values for the UDF "Analysis" :
	########################################
	'''
	#Test cronjob 
	samples = lims.get_samples()
	print len(samples)

	samples = lims.get_samples()
	analysis = []
	exception = []
	for s in samples : 
		try  :
			if s.udf['Analysis'] not in analysis :
				analysis.append(s.udf['Analysis'])
				
		except Exception as e:
			exception.append(s.name) 

	print analysis
	print "\n"
	print exception
	'''
        ############################
	#Get Micro-WGS sample info :
	############################
	
	#Filtering
	analysisType = [ 'Microbiology WGS Nextera XT'
			 ]
	# 'Rutinprov'

	microWGS_sampleTableHeaders = [ "Analysis",
					"Classification" ,
					"Date received" ,
					"Workflow started (date)",
					"Progress",
					"Workflow finished (date)",
					"Department",
					"Species",
					"Sequencing runs",
					"Desired read count",
					"Sample concentration (ng/ul)" ,
					"Library concentration (ng/ul)",
					"Library concentration (date)",
					]
	microWGS_samples = []
	for analysis in analysisType :
		microWGS_samples += lims.get_samples(udf={'Analysis' : analysis, 'Classification' : 'Rutinprov'}, projectname='Microbiology WGS 2020')
		print "got micro samples " , datetime.now()
		#Get data for sample table
		
		with open('/opt/gls/clarity/customextensions/clarityDashboard/microWGS.csv', 'w') as csvfile:
			print "opened micro csv file for writing " , datetime.now()
			fieldnames = microWGS_sampleTableHeaders
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			
			rows = []
			for s in microWGS_samples :
				row = {}
				for header in microWGS_sampleTableHeaders :
					if header == "Date received" :
						row[header] = s.date_received
					else:
						try :
							row[header] = str(s.udf[header])
						except KeyError as e:
							row[header] = "NA"
						except Exception as e:
							try:
								row[header] = s.udf[header].encode('utf-8','ignore')
							except:
								print e, type(s.udf[header])
								sys.exit(255)
									
				writer.writerow( row )
	print "finished writing csv file for micro samples " , datetime.now()
	'''
	####################
	#Get RNA-seq samples
	####################

	#Filtering
	analysisType = [ 'TruSeq Stranded mRNA - Fusion',
			 'TruSeq Stranded mRNA - Bladder',
			 'TruSeq Stranded mRNA',
			 ]
	# 'Rutinprov'
	
	RNA_sampleTableHeaders = [ "Analysis",
				   "Classification" ,
				   "Date received" ,
				   "Progress",
				   "Department",
				   "Sequencing runs",
				   "Desired read count",
				   "Diagnosis",
				   "Tissue",
				   "RIN" ,
				   "DV200",
				   "Sample concentration (ng/ul)",
				   "Nanodrop concentration (ng/ul)",
				   ]
	RNA_samples = []
	for analysis in analysisType :
		RNA_samples += lims.get_samples(udf={'Analysis' : analysis, 'Classification' : 'Rutinprov'}, projectname='TruSeq Stranded mRNA 2020')
		print "got RNA samples" ,  datetime.now()
		#Get data for sample table
		
		with open('/opt/gls/clarity/customextensions/clarityDashboard/RNA.csv', 'w') as csvfile:
			print "opened RNA csv file for writing " , datetime.now()
			fieldnames = RNA_sampleTableHeaders
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			
			rows = []
			for s in RNA_samples :
				row = {}
				for header in RNA_sampleTableHeaders :
					if header == "Date received" :
						row[header] = s.date_received
					else:
						try :
							row[header] = str(s.udf[header])
						except KeyError as e:
							row[header] = "NA"
						except Exception as e:
							try:
								row[header] = s.udf[header].encode('utf-8','ignore')
							except:
								print e, type(s.udf[header])
								sys.exit(255)
								
				writer.writerow( row ) 
	print "finished writing csv file for RNA samples " , datetime.now()

        #Get data for library conc/frag graph

	with open('/opt/gls/clarity/customextensions/clarityDashboard/RNA_libQC.csv', 'w') as csvfile:
		print "opened RNA csv libQC file for writing " , datetime.now()
		fieldnames = ["Process Date" , "Process ID" , "ProcessDate_ProcessID" , "Analysis" , "Artifact name" , "Concentration" , "Fragment length"]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		
		process_libQC = {}
		processes = lims.get_processes(type='Library Quantification - Aggregate QC v.1', projectname='TruSeq Stranded mRNA 2020')
		for process in processes :
			for input  in process.all_inputs(unique=True) :
				row = {}
				if input.samples[0].udf['Classification'] == "Rutinprov" and "mRNA" in input.samples[0].project.name :
					row["Process Date"] = process.date_run
					row["Process ID"] = process.id
					row["ProcessDate_ProcessID"] = process.date_run + "_" + process.id 
					try:
						row["Concentration"] = input.udf["Qubit concentration (ng/ul)"]
					except :
						row["Concentration"] = "N/A"
					try:
						row["Fragment length"] = input.udf["Region 1 Average Size - bp"]
					except:
						row["Fragment length"] = "N/A"
					row["Artifact name"]  = input.name
					row["Analysis"] = input.samples[0].udf["Analysis"]
					writer.writerow( row )

	print "finished writing csv file for RNA libQC " , datetime.now() 
	
	############################
	#Get Human-WGS sample info :
	############################
	
	#Filtering
	analysisType = [ 'TruSeq DNA PCR free - WGS - constitutional - single', 
			 'TruSeq DNA PCR free - WGS - constitutional - family',
			 'TruSeq DNA PCR free - WGS - somatic - paired', 
			 'TruSeq DNA PCR free - WGS - somatic - unpaired'
			 ]
	# 'Rutinprov'

	humanWGS_sampleTableHeaders = [ "Analysis", 
					"Classification" , 
					"Date received" , 
					"Progress",
					"Department", 
					"Gene list", 
					"Sample Type", 
					"Sequencing runs", 
					"Desired read count", 
					"Reference genome" ,
					"Library concentration (pM)" , 
					"Library fragment length (bp)",
				       ]
	humanWGS_samples = []
        for analysis in analysisType :
		humanWGS_samples += lims.get_samples(udf={'Analysis' : analysis, 'Classification' : 'Rutinprov'})

	#Get data for sample table
	
	with open('/opt/gls/clarity/customextensions/clarityDashboard/humanWGS.csv', 'w') as csvfile:
		print "opened humanWGS csv file for writing " , datetime.now()
		fieldnames = humanWGS_sampleTableHeaders
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		
		rows = []
		for s in humanWGS_samples :
			row = {}
			for header in humanWGS_sampleTableHeaders :
				if header == "Date received" :
					row[header] = s.date_received
				else:
					try :
						row[header] = str(s.udf[header])
					except KeyError as e:
						row[header] = "NA"
					except Exception as e:
						try:
							row[header] = s.udf[header].encode('utf-8','ignore')
						except:
							print e, type(s.udf[header])
							sys.exit(255)
			
			writer.writerow( row )
	print "finished writing csv file for humanWGS samples " , datetime.now()

	#Get data for library conc graph
	with open('/opt/gls/clarity/customextensions/clarityDashboard/humanWGS_libQC.csv', 'w') as csvfile:
		print "opened humanWGS libQC file for writing " , datetime.now()
		fieldnames = ["Process Date" , "Process ID" , "Artifact name" , "Library concentration (nM)" , "Size (bp)"] 
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames) 
		writer.writeheader()

		process_nM = {}
		processes = lims.get_processes(type='TruSeq DNA PCR free - WGS - NovaSeq sequencing v.1')
		for process in processes : 
			
			for input, output in process.input_output_maps:
				row = {}
				if input['uri'].samples[0].udf['Classification'] == "Rutinprov"  and output['output-generation-type'] == 'PerInput':
					try: 
						row["Size (bp)"] = input['uri'].udf['Size (bp)' ]
					except :
						row["Size (bp)"] = "N/A"
					try: 
						row["Process Date" ] = process.date_run
					except: 
						row["Process Date" ] = "N/A"
					
					row["Process ID"] = process.id
					row["Artifact name"] = output['uri'].name
					
					try: 
						row["Library concentration (nM)"] = output['uri'].udf['Size adjusted concentration (nM)' ] 
					except: 
						row["Library concentration (nM)"] = "N/A"
					writer.writerow( row )
	print "finished writing csv file for humanWGS libQC " , datetime.now()
        ########################
	#Get Twist sample info :
	########################
	#Filtering
	analysisType = [ 'Parad - GMSMyeloidv1.0' , 
			 'Oparad - KLL - GMSMyeloidv1.0', 
			 'Oparad - MPN - GMSMyeloidv1.0', 
			 'Oparad - AML - GMSMyeloidv1.0', 
			 'Oparad - AlloSCT - GMSMyeloidv1.0', 
			 'Oparad - Annat - GMSMyeloidv1.0', 
			 'Paired tumor exome - clinicalWESv1.0', 
			 'Single exome - clinicalWESv1.0', 
			 'Oparad - Ovarialcancer - HereditarySolidCancerv1.0', 
			 'Parad - Ovarialcancer - HereditarySolidCancerv1.0', 
			 'Onkogenetik - screening - HereditarySolidCancerv1.0', 
			 'Onkogenetik - prediktiv - HereditarySolidCancerv1.0',
			 'Oparad - GMSLymphomav1.0',
			 'Parad - GMSLymphomav1.0'
			 ]
	#'Rutinprov'
	
	twist_sampleTableHeaders = [ 'Analysis',
				     'Classification',
				     'Date received' ,
				     'Tissue',
				     'Diagnosis',
				     'Progress',
				     'Department',
				     'Gene list',
				     'Sample Type',
				     'Sequencing runs',
				     'Desired read count'
				     ]
	
	twist_samples = []
	for analysis in analysisType :
		
		twist_samples += lims.get_samples(udf={'Analysis' : analysis, 'Classification' : 'Rutinprov'})

	#udfs = []
	#for sample in twist_samples : 
	#	for key, value in sample.udf.items() : 
	#		if key not in udfs : 
	#			udfs.append(key) 
	#print udfs
	#sys.exit(255)
	

	#Get data for sample table
		
	with open('/opt/gls/clarity/customextensions/clarityDashboard/twist.csv', 'w') as csvfile:
		print "opened twist csv file for writing " , datetime.now()
		fieldnames = twist_sampleTableHeaders
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		
		rows = []
		for s in twist_samples :
			row = {}
			for header in twist_sampleTableHeaders :
				if header == "Date received" :
					row[header] = s.date_received
				else: 
					try :
						row[header] = str(s.udf[header])
					except KeyError as e: 
						row[header] = "NA"
					except Exception as e:
						try: 
							row[header] = s.udf[header].encode('utf-8','ignore')
						except: 
							print e, type(s.udf[header])
							sys.exit(255)
						
						
			writer.writerow( row )  
	print "finished writing csv file for twist samples " , datetime.now()
	#Get data for sample tapestation graph
	
	with open('/opt/gls/clarity/customextensions/clarityDashboard/twist_sampleTapestation.csv', 'w') as csvfile:
		print "opened twist sampleTapestation file for writing " , datetime.now()
		fieldnames = ["Process Date" , "Process ID" , "ProcessDate_ProcessID" ,"Artifact type" , "Analysis" , "Artifact name" , "Fragment length"]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		
		process_sampleTapestationQC = {}
		processes = lims.get_processes(type='Initial Sample Quantification - Tapestation - DNA v.1', projectname='KAPA-Twist 2020')
		for process in processes :
			for input , output in process.input_output_maps :
				if output['output-generation-type'] == 'PerInput' : 
					if input['uri'].samples[0].udf['Classification'] == "Rutinprov" and "Twist" in input['uri'].samples[0].project.name :
						row = {}
						row["Process Date"] = process.date_run
						row["Process ID"] = process.id
						row["ProcessDate_ProcessID"] = process.date_run + "_" + process.id
						row["Artifact type"] = "analyte"
						row["Analysis"] = input['uri'].samples[0].udf["Analysis"]
						row["Artifact name"]  = input['uri'].name
						try:
							row["Fragment length"] = output['uri'].udf["Region 1 Average Size - bp"]
						except :
							row["Fragment length"] = "N/A"
						writer.writerow( row )
	print "finished writing csv file for twist tapestation samples " , datetime.now() 

	#Get data for library conc graph
	
	with open('/opt/gls/clarity/customextensions/clarityDashboard/twistQC.csv', 'w') as csvfile:
		print "opened twist QC file for writing " , datetime.now()
		fieldnames = ["Process Date" , "Process ID" , "ProcessDate_ProcessID" ,"Artifact type" , "Analysis" , "Artifact name" , "Concentration" , "Fragment length"]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		
		process_libQC = {}
		processes = lims.get_processes(type='Library quantification - Aggregate QC v.2')
		for process in processes :
			for input  in process.all_inputs(unique=True) :
				row = {}
				if input.samples[0].udf['Classification'] == "Rutinprov" and "Twist" in input.samples[0].project.name :
					row["Process Date"] = process.date_run
					row["Process ID"] = process.id
					row["ProcessDate_ProcessID"] = process.date_run + "_" + process.id
					try:
						row["Concentration"] = input.udf["Qubit concentration (ng/ul)"]
					except :
						row["Concentration"] = "N/A"
					try:
						row["Fragment length"] = input.udf["Region 1 Average Size - bp"]
					except:
						row["Fragment length"] = "N/A"
						
					if len(input.samples) > 1 :
						#dealing with a pool
						row["Artifact type"] = "pool"
						row["Analysis"] = input.name.split("_")[0]
						row["Artifact name"]  = input.name
					else:
						#Dealing with individual libraries
						row["Artifact type"] = "analyte"
						row["Analysis"] = input.samples[0].udf["Analysis"]
						row["Artifact name"]  = input.name
					writer.writerow( row )
	print "finished writing csv file for twist QC " , datetime.now()
	
        ############################
	#Get NIPT data analysis info
	############################
	udfs = ["Sample Classification", "Sample Failed - Action", "NIPT test results", "NIPT report - comment", "NIPT report - free text"]
	with open('/opt/gls/clarity/customextensions/clarityDashboard/NIPT.csv', 'w') as csvfile:
		print "opened NIPT file for writing " , datetime.now()
		fieldnames = ["Process Date" , "Process ID" , "ProcessDate_ProcessID" , "Analysis" , "Artifact name" , "Sample Classification", "Sample Failed - Action", "NIPT test results", "NIPT report - comment", "NIPT report - free text"]
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		
		NIPT_data_process = {}
		processes = lims.get_processes(type=['NIPT - Clarigo Data Analysis and Report v.1.1' , 'NIPT - Clarigo Data Analysis and Report v.1'])
		for process in processes :
			for input , output in process.input_output_maps :
				if output['output-generation-type'] == 'PerInput' :
					if input['uri'].samples[0].udf['Classification'] == "Rutinprov" and "NIPT" in input['uri'].samples[0].project.name :
						row = {}
						row["Process Date"] = process.date_run
						row["Process ID"] = process.id
						row["ProcessDate_ProcessID"] = process.date_run + "_" + process.id
						row["Analysis"] = input['uri'].samples[0].udf["Analysis"]
						row["Artifact name"]  = input['uri'].name
						for udf in udfs : 
							try :
								row[udf] = str( output['uri'].udf[udf] )
							except KeyError as e:
								row[udf] = "NA"
							except Exception as e:
								try:
									row[udf] = output['uri'].udf[udf].encode('utf-8','ignore')
								except:
									print e, type( output['uri'].udf[udf] )
									sys.exit(255)
						writer.writerow( row )
	print "finished writing csv file for NIPT samples " , datetime.now()
	'''
	###########################
	#Copy csv files to lennart :
	###########################
	print "starting scp to lennart " ,  datetime.now()
	os.system("scp /opt/gls/clarity/customextensions/clarityDashboard/*.csv maryem@mtlucmds1.lund.skane.se:~/DashboardClarity2/data" )
	print "script finished " ,  datetime.now()
						
if __name__=='__main__':
	main()
