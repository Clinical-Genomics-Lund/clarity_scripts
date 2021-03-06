import sys
import os
import re
import getopt
import xml.dom.minidom
import glsapiutil
import platform
from xml.dom.minidom import parseString

HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME
api = None

def getPlacementDOM(stepURI):
    placementURI = stepURI + "/placements"
    placementURI = re.sub("http://localhost:9080", HOSTNAME, placementURI)
    placementXML = api.getResourceByURI( placementURI )
    placementDOM = parseString( placementXML )
    return placementDOM

def getAnalysis():
    placementDOM = getPlacementDOM(args["stepURI"]) 
    containerURI = conURI = placementDOM.getElementsByTagName("selected-containers")[0].getElementsByTagName("container")[0].getAttribute("uri")
    cXML = api.getResourceByURI( containerURI )
    cDOM = parseString( cXML )
    cType = cDOM.getElementsByTagName("type")[0].getAttribute( "uri" )
    cType = cType.split("/")[-1]
    
    
    IOMaps = placementDOM.getElementsByTagName( "output-placement" )
    for IOMap in IOMaps:
        iURI = IOMap.getAttribute( "uri" )
        iXML = api.getResourceByURI( iURI )
        iDOM = parseString( iXML )

        sURI = iDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
        sXML = api.getResourceByURI( sURI )
        sDOM = parseString( sXML )
        if "WGS_qPCR" in sDOM.getElementsByTagName("name")[0].firstChild.data :
            analysis = "WGS" 
        else:
            analysis = api.getUDF( sDOM, "Analysis" )
    
    return cType , analysis

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
            args[ "file" ] = p
    
    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    cType , analysis = getAnalysis()
    if  ("WGS" in analysis) :
        if  (cType == "404"):
            #start WGS input script 
            command = "/usr/bin/python  /opt/gls/clarity/customextensions/qPCR/qPCR_input_notRandom2.py -s " + args[ 'stepURI' ] + " -u " + args[ 'username' ] + " -p " + args[ 'password' ]  + " -f " + args[ "file" ]
            os.system(command)
            #print "Done"
        elif(cType == "454"):
            print("...384plate.py is running.")
            command = "/usr/bin/python  /opt/gls/clarity/customextensions/qPCR/qPCR_input_notRandom2_384.py -s " + args[ 'stepURI' ] + " -u " + args[ 'username' ] + " -p " + args[ 'password' ]  + " -f " + args[ "file" ]
            os.system(command)
        elif(cType == "554"):
            command = "/usr/bin/python  /opt/gls/clarity/customextensions/qPCR/qPCR_input_notRandom2_384_tecan.py -s " + args[ 'stepURI' ] + " -u " + args[ 'username' ] + " -p " + args[ 'password' ] + " -f " + args[ "file" ]
            os.system(command)
        
    elif (cType == "404" or cType == "454" or cType == "554") and ("WGS" not in analysis) :
        print "The selected qPCR plate is only for WGS samples. Please change to another contianer" 
        sys.exit(255) 
    
    elif ("WGS" in analysis) and ( cType != "404" and cType != "454" and cType != "554" ):
        print "Please change contianer to the WGS-specific qPCR plate"
        sys.exit(255)

    else: 
        #Start other input script
        command = "/usr/bin/python  /opt/gls/clarity/customextensions/qPCR/qPCR_input_notRandom.py -s " + args[ 'stepURI' ] + " -u " + args[ 'username' ] + " -p " + args[ 'password' ] + " -f " + args[ "file" ]
        os.system(command)

    #print "Done" 

if __name__ == "__main__":
    main()
