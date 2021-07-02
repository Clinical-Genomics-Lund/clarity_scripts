import sys
import csv
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
CACHE = {}
api = None

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]

def DOMfromURI(URI) : 
    XML = api.getResourceByURI( URI )
    DOM = parseString( XML )
    return DOM 

def getWell(wellposition):
    letter = wellposition[0]
    number = int(wellposition[1:])
    letterDict = {'A' : 0, 'B' : 12, 'C' : 24, 'D' : 36, 'E' : 48, 'F' :60, 'G' :72, 'H' : 84  }
    well = letterDict[letter] + number
    return well

def getSamples(output):
    DOM = DOMfromURI(HOSTNAME + '/api/v2/artifacts/' + output)
    sample = DOM.getElementsByTagName( "sample")[0].getAttribute("limsid")
    return sample + '_' + output

def getOutputArtifacts():
    
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME , detailsURI)
    detailsDOM = DOMfromURI(detailsURI)

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if (Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" ) :
            outputArtifacts.append(getSamples( Nodes[0].getAttribute( "limsid" )) )
        
    return outputArtifacts

def main():

    global api
    global args
    global outputArtifacts

    args = {}
    outputArtifacts = []

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:f:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-f':
            args[ "outputfile" ] = p

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    outputArtifatcts = getOutputArtifacts()

    if len(outputArtifacts) > 43:
        api.reportScriptStatus( stepURI, "ERROR", "Too many input samples. The maximum number of samples for this step is 43.")

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out)

    f_out.write('[Sample Setup]'+ '\n')
    writer.writerow( ('Well', 'Well Position', 'Sample Name', 'Biogroup Name', 'Biogroup Color', 'Target Name', 'Task' , 'Reporter', 'Quencher', 'Comments') )
    writer.writerow( ('1', 'A1', 'S1' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','6.8' ) )
    writer.writerow( ('49', 'E1', 'S1' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','6.8' ) )
    writer.writerow( ('13', 'B1', 'S2' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','0.68' ) )
    writer.writerow( ('61', 'F1', 'S2' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','0.68' ) )
    writer.writerow( ('25', 'C1', 'S3' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','0.068' ) )
    writer.writerow( ('73', 'G1', 'S3' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','0.068' ) )
    writer.writerow( ('37', 'D1', 'S4' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','0.0068' ) )
    writer.writerow( ('85', 'H1', 'S4' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','0.0068' ) )

    artifactnumber = 0
    c = 0
    b = 2
    for output in outputArtifacts :
        artifactnumber += 1
        if (artifactnumber <=40 ):
            writer.writerow((getWell((chr(ord('A')+c )+ str(b))) , chr(ord('A')+c )+ str(b), output, '' ,'' ,'','','','','' ))
            writer.writerow((getWell((chr(ord('A')+c )+ str(b+1))), chr(ord('A')+c )+ str(b+1), output, '' ,'' ,'','','','','' ))
            c+=1
            if (c==8) :
                b+=2
                c=0
        if (artifactnumber >40 ):
            b=12
            writer.writerow((getWell((chr(ord('A')+c )+ str(b))), chr(ord('A')+c )+ str(b), output, '' ,'' ,'','','','','' ))
            c+=1
            writer.writerow((getWell((chr(ord('A')+c )+ str(b))), chr(ord('A')+c )+ str(b), output, '' ,'' ,'','','','','' ))
            c+=1
                
        
    f_out.close()

if __name__ == "__main__":
    main()
