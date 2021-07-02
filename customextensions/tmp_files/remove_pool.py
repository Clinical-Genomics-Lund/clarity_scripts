import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
DEBUG = "false"
CACHE = {}
#api = None
def main():
    global api

    rXML = '<rt:routing xmlns:rt="http://genologics.com/ri/routing"><assign stage-uri="https://mtapp046.lund.skane.se/api/v2/configuration/workflows/1/stages/76"><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-476"/><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-475"/><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-474"/><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-471"/><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-470"/><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-473"/><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-472"/></assign><unassign workflow-uri="https://mtapp046.lund.skane.se/api/v2/configuration/workflows/1"><artifact uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-482"/></unassign></rt:routing>'
        
    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( "apiuser", "LateDollarsState592" )

#    print BASE_URI + "route/artifacts/"

    response = api.createObject( rXML, BASE_URI + "route/artifacts/" )

    print response

if __name__ == "__main__":
    main()
