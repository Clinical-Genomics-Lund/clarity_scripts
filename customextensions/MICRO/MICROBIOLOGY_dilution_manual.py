import sys
import csv
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

def getArtifacts():
    
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME , detailsURI)
    detailsDOM = parseString( api.GET(detailsURI) )

    artifacts = {}

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" :
            URI = Nodes[0].getAttribute( "uri" )
            DOM = parseString(api.GET(URI))
            sURI = DOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
            sDOM = parseString(api.GET(sURI))
            conc = float( api.getUDF(sDOM, "Sample concentration (ng/ul)") )
            well = DOM.getElementsByTagName( "value" )[0].firstChild.data
            if conc <= 0.2 : 
                firstSampleV = 0.0
                firstDiluentV = 0.0
                secondSampleV = 4.0
                secondDiluentV = 0.0
                artifacts[DOM] = { "Dilution 1 DNA (ul)" : firstSampleV, "Dilution 1 H2O (ul)" : firstDiluentV, "Dilution 2 DNA (ul)" : secondSampleV, "Dilution 2 H2O (ul)" : secondDiluentV} 

            elif conc < 3.0 :
                firstSampleV = 0.0
                firstDiluentV = 0.0
                secondSampleV = 4.0
                secondDiluentV = (( secondSampleV * conc) / 0.2) - secondSampleV
                artifacts[DOM] = { "Dilution 1 DNA (ul)" : firstSampleV, "Dilution 1 H2O (ul)" : firstDiluentV, "Dilution 2 DNA (ul)" : secondSampleV, "Dilution 2 H2O (ul)" : secondDiluentV} 
                
            elif conc > 15.0:
                firstSampleV = (50.0 * 3.0)/ conc
                firstDiluentV = 50.0 - firstSampleV 
                secondSampleV = 10.0
                secondDiluentV = 140.0
                artifacts[DOM] = { "Dilution 1 DNA (ul)" : firstSampleV, "Dilution 1 H2O (ul)" : firstDiluentV, "Dilution 2 DNA (ul)" : secondSampleV, "Dilution 2 H2O (ul)" : secondDiluentV}

            else :
                firstSampleV = 0.0
                firstDiluentV = 0.0 
                secondSampleV = ( 0.2 * 150.0 ) / conc
                secondDiluentV = 150.0 - secondSampleV
                artifacts[DOM] = { "Dilution 1 DNA (ul)" : firstSampleV, "Dilution 1 H2O (ul)" : firstDiluentV, "Dilution 2 DNA (ul)" : secondSampleV, "Dilution 2 H2O (ul)" : secondDiluentV}

            for UDF in artifacts[DOM].keys():
                api.setUDF( DOM, UDF, artifacts[DOM][UDF] )
                r = api.PUT( DOM.toxml().encode('utf-8'), URI )

    return artifacts

def main():

    global api
    global args

    args = {}

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:f:")

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

    artifacts = getArtifacts() 

if __name__ == "__main__":
    main()
