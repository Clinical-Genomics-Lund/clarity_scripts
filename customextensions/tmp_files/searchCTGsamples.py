# -*- coding: utf-8 -*-
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

    # CTG PIs to search for
    projects = ["CTG - Anna Andersson", 
                "CTG - Diana Karpman", 
                "CTG - Andreas Puschmann", 
                "CTG - Fredrik Mertens", 
                "CTG - Vineta Fellman", 
                "CTG - David Gisselsson", 
                "CTG - Jill Storry", 
                "CTG - Fredrik Liedberg", 
                "CTG - Thoas Fioretos", 
                "CTG - Anders Edsjö",
                "CTG - Caroline Hansen Nord",
                "CTG - Bo Nilsson",
                "CTG - Martin Sundwall",
                "CTG - Agnete Kirkeby",
                "CTG - Arne Egesten",
                "CTG - Lisa Påhlman" ]
    
    for project in projects :
        project = project.replace(" ", "+")
        xml = api.GET( HOSTNAME + "/api/v2/samples?udf.Department="+project )
        project = project.replace("+", " ")
        if xml:
            dom = parseString(xml)

            #Get all sample elements
            samples = dom.getElementsByTagName( "sample" )

            #Print sample names
            for sample in samples:
                sURI = sample.getAttribute("uri")
                sXML = api.GET( sURI )
                sDOM = parseString( sXML )
                # PI, Claritynummer ,provnummer, analys ,läsdjup 
                limsID = sample.getAttribute("limsid")
                name = sDOM.getElementsByTagName( "name" )[0].firstChild.data 
                date = sDOM.getElementsByTagName( "date-received" )[0].firstChild.data
                
                analysis = api.getUDF(sDOM, "Analysis")                    
                reads = api.getUDF(sDOM, "Desired read count")
                
                if not analysis:
                    analysis = "unknown" 
                if not reads :
                    reads = "unknown" 

                print project, "," , date , "," , limsID , "," , name , "," , analysis , "," , reads


if __name__ == "__main__":
    main()


