import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""
api = None

def setupGlobalsFromURI( uri ):

    global HOSTNAME
    global VERSION
    global BASE_URI

    tokens = uri.split( "/" )
    HOSTNAME = "/".join(tokens[0:3])
    VERSION = tokens[4]
    BASE_URI = "/".join(tokens[0:5]) + "/"

def getOutput( stepURI ) :
    detailsURI = stepURI + "/details" 
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
    detailsXML = api.GET( detailsURI )
    detailsDOM = parseString( detailsXML )
    
    Outputs = []
    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        
        if ( Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" ) :
            oURI = Nodes[0].getAttribute( "uri" )
            Outputs.append(oURI)

    return Outputs

def main():

    global api
    global args
    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "u:p:l:s:")

    for o,p in opts:
        if o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-l':
            args[ "chipType" ] = p
        elif o == '-s':
            args[ "stepURI" ] = p

    setupGlobalsFromURI( args[ "stepURI" ] )
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )
    
    Outputs = getOutput( args[ "stepURI" ] )
    for output in Outputs :
        oXML = api.GET( output )
        oDOM = parseString( oXML )
        containerURI = oDOM.getElementsByTagName( "container" )[0].getAttribute( "uri") 
        cXML = api.GET( containerURI )
        cDOM = parseString( cXML )
        containerType = cDOM.getElementsByTagName( "type" )[0].getAttribute( "name")
        
        if args[ "chipType" ] not in containerType :
            print "Detected difference between chosen container and planned Chip type. Please change container before re-starting this step"
            sys.exit(255)

if __name__ == "__main__":
    main()
