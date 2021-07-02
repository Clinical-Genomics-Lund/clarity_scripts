
"""Python interface to GenoLogics LIMS via its REST API.
Usage examples: Calculate DNA dilutions for all sample in given process.
Sima Rahimi, CMD.
"""
from genologics.lims import *
#from genologics.config import BASEURI, USERNAME, PASSWORD
#from genologics.entities import SampleHistory
import sys
import getopt


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
		elif o == '-s':
			args[ "processLuid" ] = p
	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()
	process_id = args["processLuid"]
	process = Process(lims, id=process_id)
	
	for input, output in process.input_output_maps:
		cons_value = None
		if output:
			if output['output-generation-type'] == 'PerInput':
				art=output['uri'] #art is an Atrifact object
				for key, value in  art.udf.items(): #artifact udfs
					if  key == 'Qubit concentration (ng/ul)':
						cons_value = value
					if  key == 'Total volume (ul)':
						total_value = value
				if cons_value == None: 
					sm= art.samples
					for key , value in sm[0].udf.items() :
						if key == 'Sample concentration (ng/ul)':
							cons_value= value
				dil1, buf1, dil2, buf2 = calculate_dilution(cons_value,total_value)
				art.udf['Dilution 1 DNA (ul)'] = dil1
				art.udf['Dilution 1 - Volume TE buffer (ul)'] = buf1
				art.udf['Dilution 2 DNA (ul)'] = dil2
				art.udf['Dilution 2 - Volume TE buffer (ul)'] = buf2
				art.put()
	
if __name__=='__main__':
	main()

