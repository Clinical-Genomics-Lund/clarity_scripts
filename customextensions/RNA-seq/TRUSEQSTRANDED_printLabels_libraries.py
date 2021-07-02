import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import datetime
import os
import platform
from subprocess import call


now = datetime.datetime.now()
HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME
VERSION = "v2"

count_steps = 0
CACHE = {}
api = None

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]    

#def printLabel(SampleInfoList):
#    filename = '/all/' + SampleInfoList[0] + '.zpl'
#    f = open(filename, 'w+')
#        
#    f.write('^XA\n^BY3.0,1,38\n^FO50,0\n^BQN,2,3\n^FDMM,_' + SampleInfoList[0] + '^FS\n^FO115,33^ADN,27,10^FD' + SampleInfoList[0] + '^FS\n^FO115,70^ADN,20,10^FD' + SampleInfoList[1] + '^FS\n^FO115,93^ADN,20,10^FD' + SampleInfoList[2] + '^FS\n^XZ')
#    f.close()
#    call( ['lp','-d','ZebraLabCMD-postPCR','-o','raw',filename])
#    os.remove(filename)


def printLabel(SampleInfoList):
    filename = '/all/' + SampleInfoList[0] + '.zpl'
    f = open(filename, 'w+')

    f.write('^XA\n^BY3.0,1,25\n^FO6,0\n^BQN,2,2\n^FDMM,_' + SampleInfoList[0] + '^FS\n^FO120,30^ADN,10,10^FD' + SampleInfoList[1] + '^FS\n^FO120,50^ADN,10,10^FD' + SampleInfoList[0] + '^FS\n^FO120,70^ADN,10,10^FD' + SampleInfoList[3] + '^FS\n^XZ')
    
    f.close()
    call( ['lp','-d','ZebraLabCMD','-o','raw',filename])
    os.remove(filename)

def getLabelInfo(iURI) :
    iXML = getObject( iURI )
    iDOM = parseString( iXML )
    Name = iDOM.getElementsByTagName( "name" )[0].firstChild.data
    #Get Sample LimsID
    Nodes = iDOM.getElementsByTagName( "sample" )
    sampleLimsID = Nodes[0].getAttribute( "limsid" )

    #Get IonXpress Barcode
    Nodes = iDOM.getElementsByTagName( "reagent-label" )
    Barcode = Nodes[0].getAttribute( "name" )
    Barcode = Barcode.split(" ")[1]
    #Get the date
    Date = now.strftime("%Y-%m-%d")
    SampleInfoList = [sampleLimsID, Name, Barcode, Date]
    
    return SampleInfoList

def getInputSamples():
    tmpList = []
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
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
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    InputSamples = getInputSamples()
    for LimsID in sorted(InputSamples) :
        print >>sys.stderr, "LIMSID: " + LimsID
        SampleInfoList = getLabelInfo(InputSamples[LimsID])
        printLabel(SampleInfoList)   

if __name__ == "__main__":
    main()
