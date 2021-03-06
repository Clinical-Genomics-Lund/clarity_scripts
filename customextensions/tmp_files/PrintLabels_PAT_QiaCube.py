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
api = None

def printLabel(Input):

    #Get the date
    Date = now.strftime("%Y-%m-%d")
    
    for LimsID in sorted(Input):
        filename = '/all/' + LimsID + '.zpl'
        f = open(filename, 'w+')
        
        f.write('^XA\n^CFA,25\n^FO10,20^FD' + LimsID + '^FS\n^CFA,20\n^FO10,45^FD' + Input[LimsID] + '^FS\n^FO10,65^FD' + Date + '^FS\n^XZ')
        f.close()
        call( ['lp','-d','ZebraPat','-o','raw',filename])
        os.remove(filename)

def getInputSamples():
    InputSamples = {}
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
        iXML = api.getResourceByURI( iURI )
        iDOM = parseString( iXML )
        #Get Sample LimsID
        sampleLimsID = iDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
        sampleName = iDOM.getElementsByTagName( "name" )[0].firstChild.data 
        InputSamples[sampleLimsID] = sampleName
    
    return InputSamples

def main():

    global api
    global args
    global InputSamples

    args = {}

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

    InputSamples = getInputSamples()

    printLabel(InputSamples)

if __name__ == "__main__":
    main()
