import sys
import getopt
import xml.dom.minidom
import pprint
import glsapiutil
import re
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

DEBUG = False
api = None

ARTIFACTS = None
CACHE_IDS = []
reagentLableList = []

def setupGlobalsFromURI( uri ):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split( "/" )
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"

	if DEBUG is True:
		print HOSTNAME
		print BASE_URI

def getStepConfiguration( ):

	response = ""

	if len( args[ "stepURI" ] ) > 0:
		stepXML = api.getResourceByURI( args[ "stepURI" ] )
		stepDOM = parseString( stepXML )
		nodes = stepDOM.getElementsByTagName( "configuration" )
		if nodes:
			response = nodes[0].toxml()

	return response

def cacheArtifact( limsid ):

	global CACHE_IDS

	if limsid not in CACHE_IDS:
		CACHE_IDS.append( limsid )

def prepareCache():

	global ARTIFACTS

	lXML = '<ri:links xmlns:ri="http://genologics.com/ri">'

	for limsid in CACHE_IDS:
		link = '<link uri="' + BASE_URI + 'artifacts/' + limsid + '" rel="artifacts"/>'
		lXML = lXML + link
	lXML = lXML + '</ri:links>'

	mXML = api.getBatchResourceByURI( BASE_URI + "artifacts/batch/retrieve", lXML )
	ARTIFACTS = parseString( mXML )

def getArtifact( limsid ):

	response = None

	elements = ARTIFACTS.getElementsByTagName( "art:artifact" )
	for artifact in elements:
		climsid = artifact.getAttribute( "limsid" )
		if climsid == limsid:
			response = artifact

	return response

def checkReagentLable(reagentLable) :
	global reagentLableList 
	if reagentLable not in reagentLableList :
		reagentLableList.append(reagentLable)
	else:
		print "Index name " + reagentLable + " already detected for another sample" 
		sys.exit(255)

def checkIndexes():

	## step one: get the process XML
	sURI = BASE_URI + "processes/" + args[ "limsid" ]
	sXML = api.getResourceByURI( sURI )
	sDOM = parseString( sXML )

	IOMaps = sDOM.getElementsByTagName( "input-output-map" )
	for IOMap in IOMaps:
		input = IOMap.getElementsByTagName( "input" )
		limsid = input[0].getAttribute( "limsid" )
		cacheArtifact( limsid )

	prepareCache()

	## let's dig containers out of the cache
	for limsid in CACHE_IDS:
		artifact = getArtifact( limsid )
		
		#Check indexes 
		reagentLable = artifact.getElementsByTagName( "reagent-label" )[0].getAttribute("name")
		checkReagentLable(reagentLable)

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "l:u:p:s:")

	for o,p in opts:
		if o == '-l':
			args[ "limsid" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p
		elif o == '-s':
			args[ "stepURI" ] = p

	setupGlobalsFromURI( args[ "stepURI" ] )
	api = glsapiutil.glsapiutil()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	checkIndexes()

if __name__ == "__main__":
	main()
