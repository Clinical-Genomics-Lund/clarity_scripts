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

getWell = { "A1" : "1" , "B1" : "2" , "C1" : "3" , "D1" : "4" , "E1" : "5" , "F1" : "6" , "G1" : "7" , "H1" : "8" ,
            "A2" : "9" , "B2" : "10" , "C2" : "11" , "D2" : "12" , "E2" : "13" , "F2" : "14" , "G2" : "15" , "H2" : "16" ,
            "A3" : "17" , "B3" : "18" , "C3" : "19" , "D3" : "20" , "E3" : "21" , "F3" : "22" , "G3" : "23" , "H3" : "24" ,
            "A4" : "25" , "B4" : "26" , "C4" : "27" , "D4" : "28" , "E4" : "29" , "F4" : "30" , "G4" : "31" , "H4" : "32" ,
            "A5" : "33" , "B5" : "34" , "C5" : "35" , "D5" : "36" , "E5" : "37" , "F5" : "38" , "G5" : "39" , "H5" : "40" ,
            "A6" : "41" , "B6" : "42" , "C6" : "43" , "D6" : "44" , "E6" : "45" , "F6" : "46" , "G6" : "47" , "H6" : "48" ,
            "A7" : "49" , "B7" : "50" , "C7" : "51" , "D7" : "52" , "E7" : "53" , "F7" : "54" , "G7" : "55" , "H7" : "56" ,
            "A8" : "57" , "B8" : "58" , "C8" : "59" , "D8" : "60" , "E8" : "61" , "F8" : "62" , "G8" : "63" , "H8" : "64" ,
            "A9" : "65" , "B9" : "66" , "C9" : "67" , "D9" : "68" , "E9" : "69" , "F9" : "70" , "G9" : "71" , "H9" : "72" ,
            "A10" : "73" , "B10" : "74" , "C10" : "75" , "D10" : "76" , "E10" : "77" , "F10" : "78" , "G10" : "79" , "H10" : "80" ,
            "A11" : "81" , "B11" : "82" , "C11" : "83" , "D11" : "84" , "E11" : "85" , "F11" : "86" , "G11" : "87" , "H11" : "88" ,
            "A12" : "89" , "B12" : "90" , "C12" : "91" , "D12" : "92" , "E12" : "93" , "F12" : "94" , "G12" : "95" , "H12" : "96" }

index7positions = { "p7-01" : "1" ,
                    "p7-02" : "2" ,
                    "p7-03" : "3" ,
                    "p7-04" : "4" ,
                    "p7-05" : "5" ,
                    "p7-06" : "6" ,
                    "p7-07" : "7" ,
                    "p7-08" : "8" ,
                    "p7-09" : "9" ,
                    "p7-10" : "10" ,
                    "p7-11" : "11" ,
                    "p7-12" : "12" ,
                    "p7-13" : "13" ,
                    "p7-14" : "14" ,
                    "p7-15" : "15" ,
                    "p7-16" : "16" }

index5positions = { "p5-01" : "1", 
                    "p5-02" : "2",
                    "p5-03" : "3",
                    "p5-04" : "4",
                    "p5-05" : "5",
                    "p5-06" : "6",
                    "p5-07" : "7",
                    "p5-08" : "8",
                    "p5-09" : "9",
                    "p5-10" : "10",
                    "p5-11" : "11",
                    "p5-12" : "12" }

def getOutputArtifacts():
    
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME , detailsURI)
    detailsDOM = parseString( api.GET(detailsURI) )

    outputArtifacts = {}
    ControlCheck = "no"

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if (Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" ) :
            outputDOM = parseString(api.GET( Nodes[0].getAttribute( "uri" ) ))
            name = outputDOM.getElementsByTagName( "name" )[0].firstChild.data
            if name == "NIPT - NegativeControl" :
                ControlCheck = "yes" 

            #Indexes
            index = outputDOM.getElementsByTagName( "reagent-label" )[0].getAttribute( "name" )
            p7p5 = index.split(' ')[1]
            index7 = p7p5[0:2] + "-" + p7p5[2:4]
            index5 = p7p5[5:7] + "-" + p7p5[7:9]
            indexes = []
            indexes = [index7 , index5 ] 
            
            well = outputDOM.getElementsByTagName( "value" )[0].firstChild.data
            well = well.replace(':' ,'', 1)
            well = int(getWell[well] )
            outputArtifacts[well] = indexes
        
    return outputArtifacts, ControlCheck

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

    outputArtifacts, ControlCheck = getOutputArtifacts()
    if ControlCheck == "no" :
        print "Step must contain negative control" 
        sys.exit(255)

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out, delimiter=',', quotechar="\'")
#quoting=csv.QUOTE_NONE

    writer.writerow( ('Sourcelabwarelabel', 'SourcePosition', 'DestinationLabwareLabel', 'DestinationPosition', 'Volume', ))

    for well in sorted(outputArtifacts.keys()) :
        index7pos = index7positions[outputArtifacts[well][0]]
        writer.writerow( ('1x24 Eppendorf Tube Runner no Tubes_newDef[001]', index7pos, 'Universal PCR plate' ,well ,'2' ))

    for well in sorted(outputArtifacts.keys()) :
        index5pos = index5positions[outputArtifacts[well][1]]
        writer.writerow( ('1x24 Eppendorf Tube Runner no Tubes_newDef[002]', index5pos, 'Universal PCR plate' ,well ,'2' ))

    f_out.close()

if __name__ == "__main__":
    main()
