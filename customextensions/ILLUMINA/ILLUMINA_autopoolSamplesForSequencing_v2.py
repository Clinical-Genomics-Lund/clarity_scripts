import sys
import getopt
import xml.dom.minidom
import pprint
import glsapiutil
import re
from xml.dom.minidom import parseString

DEBUG = False
api = None
ARTIFACTS = None
CACHE_IDS = []

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
		stepDOM = parseString( api.GET(args[ "stepURI" ]) )
		nodes = stepDOM.getElementsByTagName( "configuration" )
		if nodes:
			response = nodes[0].toxml()

	return response

def getPoolingGroup( aURI ):

	aDOM = parseString( api.GET(aURI) )
	pGroup = aDOM.getElementsByTagName( "name" )[0].firstChild.data.split("_")[-1]

	return pGroup

def buildGroupPoolXML( poolName, alist ):

	pXML = '<pool name="' + poolName +'">'
	for aURI in alist:
		pXML = pXML + '<input uri="' + aURI + '"/>'
	pXML = pXML + '</pool>'

	return pXML

def autoPool():
	pools = []
	pGroups = []

	## get the process XML
	dURI = BASE_URI + "steps/" + args[ "limsid" ] + "/details"
	dDOM = parseString( api.GET(dURI) )

	IOmap = dDOM.getElementsByTagName( "input-output-map" )
	for IO in IOmap:
		iURI = IO.getElementsByTagName( "input" )[0].getAttribute( "uri" )
		if iURI not in pools:
			pools.append(iURI)

	for iURI in pools:
		pGroup = getPoolingGroup( iURI )
		if pGroup not in pGroups:
			pGroups.append( pGroup )
	
	if len(pGroups) > 1 :
		print "Only allowed to sequence pools from the same normalization step"
		sys.exit(255)
	else:

		## let's build the pooling XML based upon the groups
		pXML = '<?xml version="1.0" encoding="UTF-8"?>'
		pXML = pXML + '<stp:pools xmlns:stp="http://genologics.com/ri/step" uri="' + args[ "stepURI" ] +  '/pools">'
		pXML = pXML + '<step uri="' + args[ "stepURI" ] + '"/>'
		pXML = pXML + getStepConfiguration()
		pXML = pXML + '<pooled-inputs>'

		pXML = pXML + buildGroupPoolXML( pGroups[0], pools )

		pXML = pXML + '</pooled-inputs>'
		pXML = pXML + '<available-inputs/>'
		pXML = pXML + '</stp:pools>'

		response = api.PUT( pXML, args[ "stepURI" ] + "/pools" )
		print response
		
	processURI = BASE_URI + "processes/" + args[ "limsid" ]
	processDOM = parseString( api.GET(processURI) )
	api.setUDF( processDOM, "planID", pGroups[0] )
	response = api.PUT( processDOM.toxml(), processURI )



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
	api = glsapiutil.glsapiutil2()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	autoPool()

if __name__ == "__main__":
	main()
