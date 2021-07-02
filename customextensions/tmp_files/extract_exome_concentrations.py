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
    searchURI = "https://mtapp046.lund.skane.se/api/v2/processes/?project=SureSelect+XTHS+Clinical+Exome&type=Library+Quantification+-+Qubit+-+DNA"
    searchDOM = parseString(api.GET(searchURI))
    foundProcesses = searchDOM.getElementsByTagName( "process" )
    
    for process in foundProcesses :
#        print process.getAttribute( "limsid" )
        processURI = process.getAttribute( "uri" )
        processDOM = parseString(api.GET(processURI))
        InOutMaps =  processDOM.getElementsByTagName( "input-output-map" )
        for IOMap in InOutMaps:
            Nodes = IOMap.getElementsByTagName( "output" )
            if ( Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" ) :
                oURI = Nodes[0].getAttribute( "uri" )
                oDOM = parseString(api.GET(oURI))
                Name = oDOM.getElementsByTagName( "name" )[0].firstChild.data 
                konc = api.getUDF(oDOM, "Qubit concentration (ng/ul)")
                limsID = oDOM.getElementsByTagName("sample")[0].getAttribute("limsid") 
                print limsID, ",", Name,"," ,konc
                


if __name__ == "__main__":
    main()
