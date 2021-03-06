
"""Python interface to GenoLogics LIMS via its REST API.
Usage examples: Get some samples, and sample info.
Per Kraulis, Science for Life Laboratory, Stockholm, Sweden.

"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
#from genologics.entities import SampleHistory
import sys
import getopt


args = {}

opts, extraparams = getopt.getopt(sys.argv[1:], "b:s:u:p:")

for o,p in opts:
	if o == '-b':
		args[ "BASEURI" ] = p
	elif o == '-u':
		args[ "USERNAME" ] = p
	elif o == '-p':
		args[ "PASSWORD" ] = p
	elif o == '-s':
		args[ "processLuid" ] = p
BASEURI = args["BASEURI"].split('api')[0]

lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
lims.check_version()



#*********************************************************************
#--------------------- Sample examples ----------------------------------
#*********************************************************************

#samples = lims.get_samples()   #list all samples in the Clarity system
#for note in sample.notes:
#       print 'Note', note.uri, note.content
#for file in sample.files:
#       print 'File', file.content_location
'''
samples = lims.get_samples(['s1'])
for sample in samples:
	print(sample)
	print(sample.id, sample.name, sample.date_received, sample.uri)
#	artifact = sample.artifact  #print all artifacts derived from given sample
#	print artifact.uri
'''
#project = Project(lims, id='24-14387')
#sample_name = Sample(lims, id='RAH701A6')    #Retrieve the given sample
#samples = lims.get_samples(projectlimsid=project.id)  #This can list all the samples belong to a given project
#print(samples) 


#*********************************************************************
#---------------------------- Artifact examples  -------------------
#********************************************************************

#artifacts = lims.get_artifacts(sample_name='s1') # This can list either all the artifact existing in the Lims system or the given list of sample names. 
#for artifact in artifacts:
#	print artifact, artifact.name, artifact.state,  artifact.qc_flag, artifact.items()
#artifacts = Process.result_files(Process(lims, id='24-14388'))
#artifacts = lims.get_artifacts(qc_flag='PASSED') #get artifacts with passed qc
#print len(artifacts), 'QC PASSED artifacts'
#artifacts = lims.get_batch(artifacts)  


#**********************************************************
#------------Process examples ----------------------------
#**********************************************************
process_id = args["processLuid"]
#'24-87364'
process = Process(lims, id=process_id)
#print process, process.id, process.type, process.type.name, process.udf.items()  
#for key , value in process.udf.items(): #access to the udfs belonged to the given process / = step detailes in Clarity gui
#	print(key, value)
#print process.all_inputs()
#print process.analytes()
#print process.outputs_per_input(process.all_inputs())
#print(process.all_outputs( unique=True))
#print(process.analytes())
#processes = lims.get_processes()  #list all the processes
#print len(processes), 'processes in total'          



def calculate_dilution(cons_value, total_value):
	dilution1=0
	buffer1=0
	dilution2=0
	buffer2=0

	dilution2 = (total_value * 4)  / cons_value
	if dilution2 > 30:
		dilution2 = 30
	elif dilution2 < 2:
		dilution1 = 2
		buffer1 = 18
		dilution2 = (total_value * 4 ) / (cons_value / 10)
	buffer2= total_value - dilution2
	
	return(dilution1, buffer1, dilution2, buffer2)
#print('***************** input-output-map ******************************')

for input, output in process.input_output_maps:
	cons_value = None
	#if input:

	#	print 'input:', input.items()

	if output:
            if output['output-generation-type'] == 'PerInput':
                #print('*********', output.items())
		art=output['uri'] #art is an Atrifact object
                #print('output[uri].name.....',art.name)
                #print('output uri .....', art)
		#print(art.state)
		#print('art.items', art.udf.items())
		for key, value in  art.udf.items(): #artifact udfs
			#print key , value
			if  key == 'Qubit concentration (ng/ul)':
				cons_value = value
			if  key == 'Total volume (ul)':
				total_value = value
				#print('Total value is ', total_value)
		
		if cons_value == None: 
			sm= art.samples
			#print(sm[0].udf.items())
			for key , value in sm[0].udf.items() :
				if key == 'Sample concentration (ng/ul)':
					cons_value= value
		dil1, buf1, dil2, buf2 = calculate_dilution(cons_value,total_value)
		art.udf['Dilution 1 DNA (ul)'] = dil1
		art.udf['Dilution 1 - Volume TE buffer (ul)'] = buf1
		art.udf['Dilution 2 DNA (ul)'] = dil2
		art.udf['Dilution 2 - Volume TE buffer (ul)'] = buf2
		art.put()
		
		#print(dil1, buf1, dil2, buf2)
		###art = Artifact(lims,id= output['uri'].id )
		###print('Artifact(lims,id= output[uri].id )---->',  art)
		##art.udf['Size (bp)'] = value * 100
		##art.put() #update a ud value
			 
                       


#***********************************************************
#--------------- Project examples  -------------------------
#***********************************************************

#project = Project(lims, id="ADM751") 
#print(project.items())
#print project.udf['open-date']

