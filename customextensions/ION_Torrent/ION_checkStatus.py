import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = ""
VERSION = ""
BASE_URI = ""
api = None

def setupGlobalsFromURI( uri ):

    global HOSTNAME
    global VERSION
    global BASE_URI

    tokens = uri.split( "/" )
    HOSTNAME = "/".join(tokens[0:3])
    VERSION = tokens[4]
    BASE_URI = "/".join(tokens[0:5]) + "/"

def main():

    global api
    global args
    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "u:p:l:s:")

    for o,p in opts:
        if o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-l':
            args[ "status" ] = p
        elif o == '-s' :
            args[ "stepURI" ] = p

    setupGlobalsFromURI( args[ "stepURI" ] )
    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )
    
    #First check status
    if args[ "status" ] == "FAILED" :
        print "Can not proceed when status 'FAILED'."
        sys.exit(255)
    if args[ "status" ] == "Not_calculated_yet" :
        print "Can not proceed with status 'To be calculated'. Start Normalization script."
        sys.exit(255)

if __name__ == "__main__":
    main()
