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


def main():
        
    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( "apiuser", "LateDollarsState592" )

    new_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><art:artifact xmlns:udf="http://genologics.com/ri/userdefined" xmlns:file="http://genologics.com/ri/file" xmlns:art="http://genologics.com/ri/artifact" uri="https://mtapp046.lund.skane.se/api/v2/artifacts/2-2161?state=1231" limsid="2-2161"><name>2210-17_CF_IonXpress_005</name><type>Analyte</type><output-type>Analyte</output-type><parent-process uri="https://mtapp046.lund.skane.se/api/v2/processes/24-749" limsid="24-749" /><qc-flag>UNKNOWN</qc-flag><location><container uri="https://mtapp046.lund.skane.se/api/v2/containers/27-418" limsid="27-418" /><value>1:1</value></location><working-flag>true</working-flag><sample uri="https://mtapp046.lund.skane.se/api/v2/samples/GEN51A17" limsid="GEN51A17" /><reagent-label name="IonXpress_005" /><udf:field type="Numeric" name="Concentration (ng/ml)">1460</udf:field><udf:field type="String" name="Concentration Source">Qubit quantification step</udf:field><udf:field type="Numeric" name="Normalization DNA (ul)">2</udf:field><udf:field type="Numeric" name="Normalization H2O (ul)">192.66666666666666</udf:field><workflow-stages><workflow-stage status="IN_PROGRESS" name="Pool Barcoded Libraries (Ion AmpliSeq)" uri="https://mtapp046.lund.skane.se/api/v2/configuration/workflows/2/stages/54" /></workflow-stages></art:artifact>'
    print new_XML
    #response = api.updateObject(new_XML , 'https://mtapp046.lund.skane.se/api/v2/artifacts/2-2161')

    #print response

if __name__ == "__main__":
    main()
