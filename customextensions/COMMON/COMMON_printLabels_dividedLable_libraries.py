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
api = None

def printLabel(SampleInfoList):
    filename = '/all/' + SampleInfoList[0] + '.zpl'
    f = open(filename, 'w+')
        
    f.write('^XA\n^BY3.0,1,25\n^FO2,0\n^BQN,2,\n^FDMM,_' + SampleInfoList[0] + '^FS\n^FO110,10^ADN,25,10^FD' + SampleInfoList[0] + '^FS\n^FO110,30^ADN,20,10^FD' + SampleInfoList[1].split(" ")[0] + '^FS\n^FO110,50^ADN,20,10^FD' + 'Pre-capture' + '^FS\n^FO110,70^ADN,20,10^FD' + SampleInfoList[2] + '^FS\n^XZ')
    f.close()
    call( ['lp','-d','ZebraLabCMD','-o','raw',filename])
    os.remove(filename)

def getLabelInfo(URI) :
    XML = api.GET( URI )
    DOM = parseString( XML )
    #Get Sample LimsID
    Nodes = DOM.getElementsByTagName( "sample" )
    sampleLimsID = Nodes[0].getAttribute( "limsid" )

    #Get Adapter
    Nodes = DOM.getElementsByTagName( "reagent-label" )
    Adapter = Nodes[0].getAttribute( "name" )
    
    #Get the date
    Date = now.strftime("%Y-%m-%d")
    SampleInfoList = [sampleLimsID, Adapter, Date]
    
    return SampleInfoList

def getInputSamples():
    tmpList = []
    OutputSamples = {}
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
    detailsXML = api.GET( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        oURI = Nodes[0].getAttribute( "uri" )
        if oURI not in tmpList:
            tmpList.append(oURI)
    
    for URI in tmpList:
        XML = api.GET( URI )
        DOM = parseString( XML )
        #Get Sample LimsID
        Nodes = DOM.getElementsByTagName( "sample" )
        sampleLimsID = Nodes[0].getAttribute( "limsid" )

        OutputSamples[sampleLimsID] = URI
    
    return OutputSamples

def main():

    global api
    global args

    args = {}
    SampleInfoList = []

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    #OutputSamples : key = sampleLimsId , value = OutputArtifactURI
    OutputSamples = getInputSamples()

    for LimsID in sorted(OutputSamples) :
        SampleInfoList = getLabelInfo(OutputSamples[LimsID])
        printLabel(SampleInfoList)   

if __name__ == "__main__":
    main()
