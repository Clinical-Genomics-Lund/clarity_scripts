import sys
import csv
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None

waterTroughName = "Water trough"
runnerBaseName = "EppendorfRunner"
firstDilutionPlate = "FirstDilutionPlate"
secondDilutionPlate = "SecondilutionPlate"

wellOrder = [ "1:A" , "2:A" ,  "3:A" , "4:A" , "5:A" , "6:A" , "7:A" , "8:A" , 
              "9:A" , "10:A" , "11:A" , "12:A", "13:A" , "14:A" , "15:A" , "16:A" ,
              "17:A" , "18:A" , "19:A" , "20:A" , "21:A", "22:A" , "23:A" , "24:A" ,

              "1:B" , "2:B" , "3:B" , "4:B" , "5:B" , "6:B" , "7:B" , "8:B" ,
              "9:B" , "10:B" ,  "11:B" , "12:B" , "13:B" , "14:B" , "15:B" , "16:B" ,
              "17:B" , "18:B" ,  "19:B" , "20:B" , "21:B" , "22:B" , "23:B" , "24:B" ,

              "1:C" , "2:C" ,  "3:C" , "4:C", "5:C" , "6:C" , "7:C" , "8:C",
              "9:C"  , "10:C" ,  "11:C" , "12:C" , "13:C", "14:C", "15:C", "16:C" ,
              "17:C" , "18:C" , "19:C" , "20:C" , "21:C" , "22:C" , "23:C", "24:C" ,

              "1:D" , "2:D" ,  "3:D" , "4:D" , "5:D" , "6:D" , "7:D" , "8:D" ,
              "9:D" , "10D" ,  "11:D" , "12:D" , "13:D" , "14:D" , "15:D" , "16:D" ,
              "17:D" , "18:D" ,  "19:D" , "20:D" , "21:D" , "22:D" , "23:D" , "24:D" ]

getWell = { "1:A" : "A1" , "2:A" : "B1" ,  "3:A" : "C1" , "4:A" : "D1" , "5:A" : "E1" , "6:A" : "F1" , "7:A" : "G1" , "8:A" : "H1" ,
            "9:A" : "A2" , "10:A" : "B2" ,  "11:A" : "C2" , "12:A" : "D2" , "13:A" : "E2" , "14:A" : "F2" , "15:A" : "G2" , "16:A" : "H2" ,
            "17:A" : "A3" , "18:A" : "B3" ,  "19:A" : "C3" , "20:A" : "D3" , "21:A" : "E3" , "22:A" : "F3" , "23:A" : "G3" , "24:A" : "H3" ,
            
            "1:B" : "A4" , "2:B" : "B4" ,  "3:B" : "C4" , "4:B" : "D4" , "5:B" : "E4" , "6:B" : "F4" , "7:B" : "G4" , "8:B" : "H4" ,
            "9:B" : "A5" , "10:B" : "B5" ,  "11:B" : "C5" , "12:B" : "D5" , "13:B" : "E5" , "14:B" : "F5" , "15:B" : "G5" , "16:B" : "H5" ,
            "17:B" : "A6" , "18:B" : "B6" ,  "19:B" : "C6" , "20:B" : "D6" , "21:B" : "E6" , "22:B" : "F6" , "23:B" : "G6" , "24:B" : "H6" ,
            
            "1:C" : "A7" , "2:C" : "B7" ,  "3:C" : "C7" , "4:C" : "D7" , "5:C" : "E7" , "6:C" : "F7" , "7:C" : "G7" , "8:C" : "H7" ,
            "9:C" : "A8" , "10C" : "B8" ,  "11:C" : "C8" , "12:C" : "D8" , "13:C" : "E8" , "14:C" : "F8" , "15:C" : "G8" , "16:C" : "H8" ,
            "17:C" : "A9" , "18:C" : "B9" ,  "19:C" : "C9" , "20:C" : "D9" , "21:C" : "E9" , "22:C" : "F9" , "23:C" : "G9" , "24:C" : "H9" ,
            
            "1:D" : "A10" , "2:D" : "B10" ,  "3:D" : "C10" , "4:D" : "D10" , "5:D" : "E10" , "6:D" : "F10" , "7:D" : "G10" , "8:D" : "H10" ,
            "9:D" : "A11" , "10D" : "B11" ,  "11:D" : "C11" , "12:D" : "D11" , "13:D" : "E11" , "14:D" : "F11" , "15:D" : "G11" , "16:D" : "H11" ,
            "17:D" : "A12" , "18:D" : "B12" ,  "19:D" : "C12" , "20:D" : "D12" , "21:D" : "E12" , "22:D" : "F12" , "23:D" : "G12" , "24:D" : "H12" }

def getRunnerName(well) :
    runnerID = well[-1]
    RunnerName = runnerBaseName + runnerID
    return RunnerName

def getRunnerPosition(well) :
    pos = re.split(":", well, 1)
    return pos[0]
    
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
                secondSampleV = 10.0
                secondDiluentV = 0.0
                artifacts[well] = { "firstSampleV" : firstSampleV, "firstDiluentV" : firstDiluentV, "secondSampleV" : secondSampleV, "secondDiluentV" : secondDiluentV} 
                
            elif conc >= 10.0:
                firstSampleV = 4.0
                firstDiluentV = 100.0
                firstDilutedC = ( firstSampleV * conc ) / ( firstSampleV + firstDiluentV ) 
                secondSampleV = 4.0
                secondDiluentV = (( secondSampleV * firstDilutedC) / 0.2 )- secondSampleV 
                artifacts[well] = { "firstSampleV" : firstSampleV, "firstDiluentV" : firstDiluentV, "secondSampleV" : secondSampleV, "secondDiluentV" : secondDiluentV}

            else: 
                firstSampleV = 0.0
                firstDiluentV = 0.0
                secondSampleV = 4.0
                secondDiluentV = (( secondSampleV * conc) / 0.2) - secondSampleV 
                artifacts[well] = { "firstSampleV" : firstSampleV, "firstDiluentV" : firstDiluentV, "secondSampleV" : secondSampleV, "secondDiluentV" : secondDiluentV}

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
        elif o == '-f':
            args[ "outputfile" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    artifacts = getArtifacts() 
    # { "firstSampleV" : firstSampleV, "firstDiluentV" : firstDiluentV, "secondSampleV" : secondSampleV, "secondDiluentV" : secondDiluentV}

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out, delimiter=',', quotechar="\'")

    writer.writerow( ('Sourcelabwarelabel', 'SourcePosition', 'DestinationLabwareLabel', 'DestinationPosition', 'Volume', ))

    for well in wellOrder :
        if well in artifacts.keys() :
            if artifacts[well]["firstSampleV"] != 0.0 :
                writer.writerow( (getRunnerName(well), getRunnerPosition(well), firstDilutionPlate , getWell[well] , "{0:.2f}".format( artifacts[well]["firstSampleV"] ) ))

    for well in wellOrder : 
        if well in artifacts.keys() :
            if artifacts[well]["firstDiluentV"] != 0.0 :
                writer.writerow( (waterTroughName, "1:1", firstDilutionPlate , getWell[well] , "{0:.2f}".format( artifacts[well]["firstDiluentV"] ) ))
            
    for well in wellOrder :
        if well in artifacts.keys() :
            writer.writerow( (getRunnerName(well), getRunnerPosition(well), secondDilutionPlate , getWell[well] , "{0:.2f}".format( artifacts[well]["secondSampleV"] ) )) 

    for well in wellOrder :
        if well in artifacts.keys() :
            writer.writerow( (waterTroughName, "1:1", secondDilutionPlate , getWell[well] , "{0:.2f}".format( artifacts[well]["secondDiluentV"] ) )) 

    f_out.close()

if __name__ == "__main__":
    main()
