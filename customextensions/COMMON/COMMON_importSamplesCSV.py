"""Python interface to GenoLogics LIMS via its REST API.
"""
from genologics.lims import *
import sys
import getopt
import datetime
import csv 
import pprint
import urllib
import re
import CMDfunc

def createContainer( cType, cName , lims):
	c = ""
	
	cTypes = lims.get_container_types( name=cType)
	if len(cTypes) == 1 : 
		c = lims.create_container( cTypes[0], name=cName)
	return c

def processRows(ROWS, allProjectIDs, lims, nrLines):
	ContainersCreatedCache = {}
	header = ROWS[0].keys()
	projects = []

	for row in ROWS:
		try:
			sName = row[ "Submitted Sample Name" ].strip()
			projectName = row[ "ProjectName" ].strip()

			if projectName not in projects:
				projects.append(projectName)

			project = Project(lims, id = allProjectIDs[projectName]) 

			#Only existing project allowed!
			if projectName not in allProjectIDs :
				print "WARNING: Project name not available in LIMS: " , projectID
				sys.exit(255) 
			#Assume samples are placed in tubes 
			try: 
				cName = row[ "ContainerName" ].strip()
			except: 
				cName = ""

			try:
				wp = row[ "Well" ].strip()
				cType = row[ "ContainerType" ].strip()
			except:
				wp = "1:1"
				cType = "Tube"

			if len(lims.get_containers(name=cName)) == 0:
				sContainer = createContainer( cType, cName, lims )
			else:
				sContainer = lims.get_containers(name=cName)[0]
			## let's get the udfs
			udfs = {}
			for colName in header:
				if re.search("UDF/", colName):
					udfName = colName.replace( "UDF/", "" )
					udfs[ udfName ] = row[ colName ]

			#Create the sample 
			r = Sample.create(lims, 
			      container = sContainer , 
			      position = wp , 
			      project= project , 
			      name= sName , 
			      udf=udfs )

			print r

		except:
			mailStr = '\tCOMMON_importSamplesCSV.py\n\nFailed on row:\n'

			for key in row:
				mailStr = mailStr + '\t' + key + '\t: ' + str(row[key]) + '\n'

			CMDfunc.send_fail_email( mailStr )
			sys.exit(255)

	CMDfunc.send_success_email( projects, nrLines )
	sys.exit(255)
						
def getROWS( CSVfile) : 
	ROWS = []
	reader = csv.DictReader(open(CSVfile, 'rb'), delimiter=';')
	line_count = 0
	for line in reader:
		line_count +=1 
		ROWS.append(line)

	print "Number of processed lines: " , line_count
	#pprint.pprint(ROWS)
				
	return ROWS, line_count

def getToday() : 
	now = datetime.datetime.now()
	
	strToday = str(now.year) + "-"
	tmp = str(now.month)
	if len(tmp) == 1:
		tmp = "0" + tmp
	strToday += ( tmp + "-" )
	tmp = str(now.day)
	if len(tmp) == 1:
		tmp = "0" + tmp
	strToday += tmp
	
	return strToday

def main():
	global args
	args = {}
	opts, extraparams = getopt.getopt(sys.argv[1:], "b:u:p:f:")
	for o,p in opts:
		if o == '-b':
			args[ "BASEURI" ] = p
		elif o == '-u':
			args[ "USERNAME" ] = p
		elif o == '-p':
			args[ "PASSWORD" ] = p
		elif o == '-f':
			args[ "CSVfile" ] = p

	BASEURI = args["BASEURI"].split('api')[0]

	lims = Lims(BASEURI, args["USERNAME"], args["PASSWORD"])
	lims.check_version()

	TODAY = getToday()
	ROWS, nrLines = getROWS(args[ "CSVfile" ])
	allProjects = lims.get_projects()
	allProjectIDs = {}
	for project in allProjects :
		allProjectIDs[project.name] = project.id

	processRows(ROWS, allProjectIDs, lims, nrLines)

				
if __name__=='__main__':
	main()

