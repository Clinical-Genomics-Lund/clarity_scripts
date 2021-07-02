import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None

def getOutput() :
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
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
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )
    
    Outputs = getOutput()
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
