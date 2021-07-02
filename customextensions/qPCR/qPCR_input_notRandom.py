import sys
import csv
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

def getWellDuplicate(wellposition, switch) :
    if switch == 'OFF' :
        letter = wellposition[0]
        number = int(wellposition[1:]) + 1
        wellDuplicate = letter + str(number)

    elif switch == 'ON' : 
        if wellposition == 'A12':
            wellDuplicate = 'D12'
        elif wellposition == 'B12':
            wellDuplicate = 'E12'
        elif wellposition == 'C12':
            wellDuplicate = 'F12'

    return wellDuplicate

def getWell(wellposition):
    letter = wellposition[0]
    number = int(wellposition[1:])
    letterDict = {'A' : 0, 'B' : 12, 'C' : 24, 'D' : 36, 'E' : 48, 'F' :60, 'G' :72, 'H' : 84  }
    well = letterDict[letter] + number
    return well

def getSamples(output):
    DOM = parseString( api.GET(HOSTNAME + '/api/v2/artifacts/' + output))
    sample = DOM.getElementsByTagName( "sample")[0].getAttribute("limsid")
    return sample

def getOutputArtifacts():
    
    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME , detailsURI)
    detailsDOM = parseString( api.GET(detailsURI) )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if (Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" ) :
            outputDOM = parseString(api.GET( Nodes[0].getAttribute( "uri" ) ))
            well = outputDOM.getElementsByTagName( "value" )[0].firstChild.data
            well = well.replace(':' ,'', 1)
            outputArtifacts[(getSamples( Nodes[0].getAttribute( "limsid" )) )] = well
        
    return outputArtifacts

def main():

    global api
    global args
    global outputArtifacts

    args = {}
    outputArtifacts = {}

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

    setupGlobalsFromURI( args[ "stepURI" ] )
    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    outputArtifatcts = getOutputArtifacts()

    if len(outputArtifacts) > 43:
        api.reportScriptStatus( stepURI, "ERROR", "Too many input samples. The maximum number of samples for this step is 43.")

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out, delimiter=',', quotechar="\'")
#quoting=csv.QUOTE_NONE
    f_out.write('[Sample Setup]'+ '\n')
    writer.writerow( ('Well', 'Well Position', 'Sample Name', 'Biogroup Name', 'Biogroup Color', 'Target Name', 'Task' , 'Reporter', 'Quencher', 'Quantity' ,'Comments') )
    writer.writerow( ('1', 'A1', 'S1' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"6.8"','' ) )
    writer.writerow( ('49', 'E1', 'S1' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"6.8"', '') )
    writer.writerow( ('13', 'B1', 'S2' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"0.68"', '') )
    writer.writerow( ('61', 'F1', 'S2' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"0.68"', '') )
    writer.writerow( ('25', 'C1', 'S3' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"0.068"','' ) )
    writer.writerow( ('73', 'G1', 'S3' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"0.068"','' ) )
    writer.writerow( ('37', 'D1', 'S4' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"0.0068"','' ) )
    writer.writerow( ('85', 'H1', 'S4' ,'' ,'' ,'Target 1','STANDARD','FAM','NFQ-MGB','"0.0068"', '') )
   
    switch = 'OFF'

    for key in outputArtifacts :
        if (outputArtifacts[key] == 'A12' or outputArtifacts[key] == 'B12' or outputArtifacts[key] == 'C12'):
            switch = 'ON'
            writer.writerow((getWell(outputArtifacts[key]) , outputArtifacts[key], key, '' ,'' ,'Target 1','UNKNOWN','FAM','NFQ-MGB','', '' ))
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], switch)  ), getWellDuplicate(outputArtifacts[key], switch), key, '' ,'' ,'Target 1','UNKNOWN','FAM','NFQ-MGB','', '' ))

        else :
            switch = 'OFF'
            writer.writerow((getWell(outputArtifacts[key]) , outputArtifacts[key], key, '' ,'' ,'Target 1','UNKNOWN','FAM','NFQ-MGB','', '' ))
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], switch)  ), getWellDuplicate(outputArtifacts[key], switch), key, '' ,'' ,'Target 1','UNKNOWN','FAM','NFQ-MGB','', '' ))   

    writer.writerow( ('84', 'G12', 'NTC' ,'' ,'' ,'Target 1','NTC','FAM','NFQ-MGB','', '') )
    writer.writerow( ('96', 'H12', 'NTC' ,'' ,'' ,'Target 1','NTC','FAM','NFQ-MGB','', '') )
    f_out.close()

if __name__ == "__main__":
    main()
