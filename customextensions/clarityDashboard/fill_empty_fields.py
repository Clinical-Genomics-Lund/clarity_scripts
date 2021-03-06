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

	
	#OBS!!!!! Sortera pa datum!!


	processes = lims.get_processes(type='Microbiology - Data Analysis v.1', projectname='Microbiology WGS 2020')
	#remove duplicates
	processes = set(processes)
	processes = sorted(processes, key = lambda i: i.date_run)
	
	for process in processes : 
		try :
			date = process.date_run
		except :
			date = ""
		print process , date

		for input  in process.all_inputs(unique=True) :
			sample = input.samples[0]
			sample.udf['Workflow finished (date)'] =  str(date)
			sample.put()


if __name__=='__main__':
	main()
