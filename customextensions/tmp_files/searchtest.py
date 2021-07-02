import sys
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'



def main():

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( "apiuser", "LateDollarsState592")

    # Personal identity number to search for
    pid = "19850106-3542"

    xml = api.GET( HOSTNAME + "/api/v2/samples?udf.Analysis=Clarigo+NIPT+Analys&udf.Personal+Identity+Number="+pid )

    if xml:
        dom = parseString(xml)

        # Get all sample elements
        samples = dom.getElementsByTagName( "sample" )

        # Print sample names
        for sample in samples:
            print sample.getAttribute("limsid")
                                



if __name__ == "__main__":
    main()


