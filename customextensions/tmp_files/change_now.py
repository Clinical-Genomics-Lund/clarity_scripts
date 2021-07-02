import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
CACHE = {}

def main():
    api = None
    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( "apiuser", "LateDollarsState592" )

    new_XML = ''

    print new_XML
    response = api.updateObject(new_XML , 'https://mtapp046.lund.skane.se/api/v2/artifacts/2-274158')
    print response

if __name__ == "__main__":
    main()
