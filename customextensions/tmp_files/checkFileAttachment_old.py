import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
DEBUG = "false"
CACHE = {}
api = None

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]    

def checkFileAttachment(oURI) :
    oXML = getObject( oURI )
    oDOM = parseString( oXML )

    #Get the Classification
    elements = oDOM.getElementsByTagName( "udf:field" )
    for udf in elements:
        temp = udf.getAttribute( "name" )
        if temp == 'Sample Classification':
            Classification = udf.firstChild.data.encode('UTF-8')

            if "Rutinprov - Godk" in Classification :
                #Get the file node
                if not oDOM.getElementsByTagName( "file:file" ):
                    stepURI = args[ "stepURI" ]
                    stepURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", stepURI)
                    api.reportScriptStatus( stepURI, "ERROR", "Result file must be uploaded")

def getInputSamples():

    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        oURI = Nodes[0].getAttribute( "uri" )
        InputSamples.append(oURI)
    
    return InputSamples

def main():

    global api
    global args
    global InputSamples

    args = {}
    InputSamples = []

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    ## at this point, we have the parameters the EPP plugin passed, and we have network plumbing
    ## so let's get this show on the road!

    InputSamples = getInputSamples()

    for oURI in InputSamples :
        checkFileAttachment(oURI)

if __name__ == "__main__":
    main()
