import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import datetime
import os
from subprocess import call


now = datetime.datetime.now()
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

def printLabel(SampleInfoList):
    filename = '/all/' + SampleInfoList[0] + '.zpl'
    f = open(filename, 'w+')
        
    f.write('^XA\n^BY3.0,1,38\n^FO50,0\n^BQN,2,3\n^FDMM,_' + SampleInfoList[0] + '^FS\n^FO125,33^ADN,27,15^FD' + SampleInfoList[0] + '^FS\n^FO125,70^ADN,20,10^FD' + SampleInfoList[1] + '^FS\n^FO125,93^ADN,20,10^FD' + SampleInfoList[2] + '^FS\n^XZ')
    f.close()
    call( ['lp','-d','ZebraLabCMD','-o','raw',filename])
    os.remove(filename)

def getLabelInfo(iURI) :
    iXML = getObject( iURI )
    iDOM = parseString( iXML )
    #Get Sample LimsID
    Nodes = iDOM.getElementsByTagName( "sample" )
    sampleLimsID = Nodes[0].getAttribute( "limsid" )

    #Get IonXpress Barcode
    #Nodes = iDOM.getElementsByTagName( "reagent-label" )
    Barcode = 'TEST'
    
    #Get the date
    Date = now.strftime("%Y-%m-%d")
    SampleInfoList = [sampleLimsID, Barcode, Date]
    
    return SampleInfoList

def getInputSamples():
    tmpList = []
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", "https://mtapp046.lund.skane.se", detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "input" )
        iURI = Nodes[0].getAttribute( "uri" )
        tmpList.append(iURI)
    
    for iURI in tmpList:
        iXML = getObject( iURI )
        iDOM = parseString( iXML )
        #Get Sample LimsID
        Nodes = iDOM.getElementsByTagName( "sample" )
        sampleLimsID = Nodes[0].getAttribute( "limsid" )

        InputSamples[sampleLimsID] = iURI
    
    return InputSamples

def main():

    global api
    global args
    global InputSamples

    args = {}
    InputSamples = {}
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

    InputSamples = getInputSamples()
    for LimsID in sorted(InputSamples) :
        print >>sys.stderr, "LIMSID: " + LimsID
        SampleInfoList = getLabelInfo(InputSamples[LimsID])
        printLabel(SampleInfoList)   

if __name__ == "__main__":
    main()
