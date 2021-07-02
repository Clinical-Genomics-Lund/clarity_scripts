import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
CACHE = {}

def main():
    api = None
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( "apiuser", "LateDollarsState592" )
    
    searchURI = "https://mtapp046.lund.skane.se/api/v2/processes/?type=Oncomine+Focus+-+Data+Analysis"
    searchDOM = parseString(api.GET(searchURI))
    foundProcesses = searchDOM.getElementsByTagName( "process" )
    
    for process in foundProcesses :
        #print process.getAttribute( "limsid" )
        processURI = process.getAttribute( "uri" )
        processDOM = parseString(api.GET(processURI))
        #print processDOM.getElementsByTagName("date-run")[0].firstChild.data
        InOutMaps =  processDOM.getElementsByTagName( "input-output-map" )
        for IOMap in InOutMaps:
            Nodes = IOMap.getElementsByTagName( "output" )
            if ( Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" ) :
                oURI = Nodes[0].getAttribute( "uri" )
                oDOM = parseString(api.GET(oURI))
                PAD = oDOM.getElementsByTagName("name")[0].firstChild.data
                FAILED = api.getUDF(oDOM, "Sample Classification")
                if "Rutinprov - Godk" not in FAILED:
                    limsID = oDOM.getElementsByTagName("sample")[0].getAttribute("limsid") 
                    sampleURI = "https://mtapp046.lund.skane.se/api/v2/samples/" + limsID
                    sampleDOM = parseString(api.GET(sampleURI))
                    sampleConc = api.getUDF(sampleDOM, "Sample concentration (ng/ul)")
                    DV200 = api.getUDF(sampleDOM, "DV200")
                    print process.getAttribute( "limsid" )   
                    print processDOM.getElementsByTagName("date-run")[0].firstChild.data
                    print PAD, ",", FAILED.encode('utf-8'), ",", limsID, sampleConc, DV200

if __name__ == "__main__":
    main()
