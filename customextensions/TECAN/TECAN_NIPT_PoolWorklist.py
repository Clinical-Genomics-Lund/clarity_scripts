import sys
import csv
import re
import getopt
import xml.dom.minidom
import glsapiutil
import platform
from xml.dom.minidom import parseString

HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None

getWell = {"A1" : "1" , "B1" : "2" , "C1" : "3" , "D1" : "4" , "E1" : "5" , "F1" : "6" , "G1" : "7" , "H1" : "8" ,
           "A2" : "9" , "B2" : "10" , "C2" : "11" , "D2" : "12" , "E2" : "13" , "F2" : "14" , "G2" : "15" , "H2" : "16" ,
           "A3" : "17" , "B3" : "18" , "C3" : "19" , "D3" : "20" , "E3" : "21" , "F3" : "22" , "G3" : "23" , "H3" : "24" ,
           "A4" : "25" , "B4" : "26" , "C4" : "27" , "D4" : "28" , "E4" : "29" , "F4" : "30" , "G4" : "31" , "H4" : "32" ,
           "A5" : "33" , "B5" : "34" , "C5" : "35" , "D5" : "36" , "E5" : "37" , "F5" : "38" , "G5" : "39" , "H5" : "40" ,
           "A6" : "41" , "B6" : "42" , "C6" : "43" , "D6" : "44" , "E6" : "45" , "F6" : "46" , "G6" : "47" , "H6" : "48" ,
           "A7" : "49" , "B7" : "50" , "C7" : "51" , "D7" : "52" , "E7" : "53" , "F7" : "54" , "G7" : "55" , "H7" : "56" ,
           "A8" : "57" , "B8" : "58" , "C8" : "59" , "D8" : "60" , "E8" : "61" , "F8" : "62" , "G8" : "63" , "H8" : "64" ,
           "A9" : "65" , "B9" : "66" , "C9" : "67" , "D9" : "68" , "E9" : "69" , "F9" : "70" , "G9" : "71" , "H9" : "72" ,
           "A10" : "73" , "B10" : "74" , "C10" : "75" , "D10" : "76" , "E10" : "77" , "F10" : "78" , "G10" : "79" , "H10" : "80",
           "A11" : "81" , "B11" : "82" , "C11" : "83" , "D11" : "84" , "E11" : "85" , "F11" : "86" , "G11" : "87" , "H11" : "88",
           "A12" : "89" , "B12" : "90" , "C12" : "91" , "D12" : "92" , "E12" : "93" , "F12" : "94" , "G12" : "95" , "H12" : "96" }


def getArtifacts():
    
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME , detailsURI)
    detailsDOM = parseString( api.GET(detailsURI) )

    outputArtifacts = {}
    volume = ""

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" :
            outputURI = Nodes[0].getAttribute( "uri" )
            outputDOM = parseString(api.GET(outputURI))
            volume = api.getUDF( outputDOM, "Volume for Pooling (ul)" )
            volume = float(volume)
            volume = round(volume, 2)
            inputURI = IOMap.getElementsByTagName( "input" )[0].getAttribute( "uri" )
            inputDOM = parseString(api.GET(inputURI))
            well = inputDOM.getElementsByTagName( "value" )[0].firstChild.data
            well = well.replace(':' ,'', 1)
            well = int( getWell[well] )
            
            outputArtifacts[well] = volume
        
    return outputArtifacts

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
        elif o == '-f':
            args[ "outputfile" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    Artifacts = getArtifacts()

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out, delimiter=',', quotechar="\'")
#quoting=csv.QUOTE_NONE

    writer.writerow( ('Sourcelabwarelabel', 'SourcePosition', 'DestinationLabwareLabel', 'DestinationPosition', 'Volume', ))

    for well in sorted(Artifacts.keys()) :
        writer.writerow( ('Pooling plate', well, '5 Eppendorf Insert [001]' ,1 ,Artifacts[well] ))

    f_out.close()

if __name__ == "__main__":
    main()
