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

def TapestationWarning( stepURI ):
	Inputs = []
	tmp = [] 

	detailsURI = stepURI + "/details"
	detailsURI = re.sub("http://localhost:9080", HOSTNAME , detailsURI)
	detailsXML = api.GET( detailsURI )
	detailsDOM = parseString( detailsXML )

	#Get inputs
	IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
	for IOMap in IOMaps :
		iURI = IOMap.getElementsByTagName( "input" )[0].getAttribute( "uri" )
		if iURI not in Inputs :
			Inputs.append(iURI)
			iXML = api.GET( iURI )
			iDOM = parseString( iXML )
			
			sURI = iDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
			sLimsID = iDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
			sXML = api.GET( sURI )
			sDOM = parseString( sXML )
			
			sConc = api.getUDF(sDOM, "Sample concentration (ng/ul)")
			if sConc != "" :
				if ( float(sConc) > 100 ) :
					tmp.append( sLimsID )
				
	string = "OBS! Prover med RNA koncentration > 100 ng/ul : " 
	string += " ".join(tmp) 

	if len(tmp) >= 1 :
		api.reportScriptStatus( args[ "stepURI" ], "OK", string )  

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "u:p:s:")

	for o,p in opts:
		if o == '-u':
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

	TapestationWarning( args[ "stepURI" ] )

if __name__ == "__main__":
	main()
