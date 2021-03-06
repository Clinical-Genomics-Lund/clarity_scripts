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
import glsfileutil

now = datetime.datetime.now()
HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
DEBUG = "false"
CACHE = {}
api = None

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]    

def printLabel(artifact):
    filename = '/all/' + artifact + '.zpl'
    f = open(filename, 'w+')
    Date = now.strftime("%Y-%m-%d")

    f.write('^XA\n^BY3.0,1,25\n^FO17\n^BQN,2,2\n^FDMM,' + artifact + '^FS\n^CFA,20\n^FO120,20^FD' + artifact + '^FS\n^CFA,20\n^FO120,50^FD' + Date + '^FS\n^XZ' )

    f.close()
    call( ['lp','-d','ZebraLabCMD','-o','raw',filename])
    os.remove(filename)

def downloadfile( file_art_luid ):
    aURI = BASE_URI + "artifacts/" + file_art_luid
    aXML = api.GET(aURI)
    aDOM = parseString(aXML)
    fURI = aDOM.getElementsByTagName( "file:file" )[0].getAttribute( "uri" )

    fDOM = parseString(api.GET(fURI))
    fileName = fDOM.getElementsByTagName("original-location")[0].firstChild.data
    if ".txt" not in fileName:
        print "The prinList must be a .txt file"
        sys.exit(255)

    newName = str( file_art_luid ) + ".txt"
    FH.getFile( file_art_luid, newName )
    raw = open( newName, "r")
    lines = raw.readlines()
    raw.close
    return lines

def parseinputFile():

    data = downloadfile( args["iFile"] )
    
    sampleIDs = []
    for row in data:
        sampleIDs.append(row.rstrip() )

    return sampleIDs
                                                                        
def main():

    global api
    global args
    global FH

    args = {}

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:f:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-f':
            args["iFile"] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    FH = glsfileutil.fileHelper()
    FH.setAPIHandler( api )
    FH.setAPIAuthTokens( args[ "username" ], args[ "password" ] )
            
    artifactsToPrint = parseinputFile()

    for artifact in sorted(artifactsToPrint) :
        print >>sys.stderr, artifact
        printLabel(artifact)  

if __name__ == "__main__":
    main()
