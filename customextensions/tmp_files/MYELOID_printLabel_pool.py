import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import os
from subprocess import call

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
count_steps = 0
DEBUG = "false"
CACHE = {}
api = None

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]    

def printLabel(LimsID, OutputName):
    filename = '/all/' + LimsID + '.zpl'
    f = open(filename, 'w+')

    f.write('^XA\n^BY3.0,1,38\n^FO50,0\n^BQN,2,3\n^FDMM, ' + LimsID + '^FS\n^FO125,33^ADN,30,10^FD' + LimsID + '^FS\n^FO125,70^ADN,30,10^FD' + OutputName + '^FS\n^XZ')
    f.close()
    call( ['lp','-d','ZebraLabCMD','-o','raw',filename])
    os.remove(filename)

def getOutputSamples():
    tmpList = []
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if Nodes[0].getAttribute( "type" ) == "Analyte" : 
            oURI = Nodes[0].getAttribute( "uri" )
            oLimsID = Nodes[0].getAttribute( "limsid" )
            oXML = getObject( oURI )
            oDOM = parseString( oXML )
            #Get the Pool Name
            PoolName = oDOM.getElementsByTagName("name")[0].firstChild.data
            OutputSamples[oLimsID] = PoolName
    return OutputSamples

def main():

    global api
    global args
    global OutputSamples

    args = {}
    OutputSamples = {}
    SampleInfoList = []

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

    OutputSamples = getOutputSamples()
    for LimsID in sorted(OutputSamples) :
        printLabel(LimsID,OutputSamples[LimsID])

if __name__ == "__main__":
    main()
