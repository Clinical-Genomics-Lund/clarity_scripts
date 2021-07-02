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
 
def getInputArtifacts(detailsURI):
    InputSamples = []
    detailsDOM = parseString( api.GET(detailsURI) )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        if iURI not in InputSamples:
            InputSamples.append(iURI)
        
    return InputSamples

def main():

    global api
    global args

    args = {}

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    setupGlobalsFromURI( args[ "stepURI" ] )
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    stepURI = re.sub("http://localhost:9080", HOSTNAME, args[ "stepURI" ])
    detailsURI = stepURI + "/details"

    inputArtifacts = getInputArtifacts(detailsURI)
    names = []

    for iURI in inputArtifacts:
        iXML = api.GET(iURI)
        iDOM = parseString(iXML)
        name = iDOM.getElementsByTagName("name")[0].firstChild.data

        #Check Name
        if name not in names:
            names.append(name)
        else :
            print "All sample names must be unique"
            sys.exit(255)

        if "_" in name:
            print "Sample name must not contain underscore '_'"
            sys.exit(255)
        elif "/" in name:
            print "Sample name must not contain slash '/'"
            sys.exit(255)
        elif " " in name:
            print "Sample name must not contain space ' '"
            sys.exit(255)
        elif "." in name:
            print "Sample name must not contain dot '.'"
            sys.exit(255)

        #Check PersonalIdentityNumber
        sURI = iDOM.getElementsByTagName("sample")[0].getAttribute("uri")
        sDOM =  parseString( api.GET(sURI) )
        PNR = api.getUDF(sDOM, "Personal Identity Number")

        if PNR != "" :
            t = re.match("^[0-9]{8}-[0-9a-zA-Z]{4}$",PNR)
            if t == None :
                print name + ": Please make sure that Personal Identity Number is given in the following format: YYYYMMDD-XXXX"
                sys.exit(255)

if __name__ == "__main__":
    main()
