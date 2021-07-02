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

def getWellDuplicate(wellposition,duplicate, switch) :
    if switch == 'OFF' :
        letter = wellposition[0]
        number = int(wellposition[1:]) + int(duplicate)
        wellDuplicate = letter + str(number)

    elif switch == 'ON' : 
        if duplicate == 1.0 :
            if wellposition == 'A11':
                wellDuplicate = 'B11'
            elif wellposition == 'C11':
                wellDuplicate = 'D11'
            elif wellposition == 'E11':
                wellDuplicate = 'F11'
            elif wellposition == 'G11':
                wellDuplicate = 'H11'
        elif duplicate == 2.0 :
            if wellposition == 'A11':
                wellDuplicate = 'A12'
            elif wellposition == 'C11':
                wellDuplicate = 'C12'
            elif wellposition == 'E11':
                wellDuplicate = 'E12' 
            elif wellposition == 'G11':
                wellDuplicate = 'G12' 
        elif duplicate == 3.0 :
            if wellposition == 'A11':
                wellDuplicate = 'B12'
            elif wellposition == 'C11':
                wellDuplicate = 'D12'
            elif wellposition == 'E11':
                wellDuplicate = 'F12'  
            elif wellposition == 'G11':
                wellDuplicate = 'H12'  

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

    outputArtifacts = getOutputArtifacts()

    if len(outputArtifacts) > 20:
        api.reportScriptStatus( stepURI, "ERROR", "Too many input samples. The maximum number of samples for this step is 20.")

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out, delimiter=',', quotechar="\'", quoting=csv.QUOTE_NONE)

    f_out.write('[Sample Setup]'+ '\n')
    writer.writerow( ('Well', 'Well Position', 'Sample Name', 'Biogroup Name', 'Biogroup Color', 'Target Name', 'Task' , 'Reporter', 'Quencher', 'Quantity' ,'Comments') )
    writer.writerow( ('1', 'A1', 'ST1' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"20.0"','' ) )
    writer.writerow( ('13', 'B1', 'ST2' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"2.0"', '') )
    writer.writerow( ('25', 'C1', 'ST3' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.2"', '') )
    writer.writerow( ('37', 'D1', 'ST4' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.02"', '') )
    writer.writerow( ('49', 'E1', 'ST5' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.002"','' ) )
    writer.writerow( ('61', 'F1', 'ST6' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.0002"','' ) )
    writer.writerow( ('73', 'G1', 'NTC' ,'' ,'' ,'Target 1','NTC','SYBR','None','','' ) ) 
   

    writer.writerow( ('2', 'A2', 'ST1' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"20.0"','' ) )
    writer.writerow( ('14', 'B2', 'ST2' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"2.0"', '') )
    writer.writerow( ('26', 'C2', 'ST3' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.2"', '') )
    writer.writerow( ('38', 'D2', 'ST4' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.02"', '') )
    writer.writerow( ('50', 'E2', 'ST5' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.002"','' ) )
    writer.writerow( ('62', 'F2', 'ST6' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.0002"','' ) )
    writer.writerow( ('74', 'G2', 'NTC' ,'' ,'' ,'Target 1','NTC','SYBR','None','','' ) )

    switch = 'OFF'

    for key in outputArtifacts :
        if (outputArtifacts[key] == 'A11' or outputArtifacts[key] == 'C11' or outputArtifacts[key] == 'E11' or outputArtifacts[key] == 'G11'):
            switch = 'ON'
            writer.writerow((getWell(outputArtifacts[key]) , outputArtifacts[key], key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))

            duplicate = 1.0
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], duplicate, switch)  ), getWellDuplicate(outputArtifacts[key], duplicate, switch), key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))

            duplicate = 2.0
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], duplicate, switch)  ), getWellDuplicate(outputArtifacts[key], duplicate, switch), key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))

            duplicate = 3.0
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], duplicate, switch)  ), getWellDuplicate(outputArtifacts[key], duplicate, switch), key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))

        else :
            switch = 'OFF'
            writer.writerow((getWell(outputArtifacts[key]) , outputArtifacts[key], key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))
            
            duplicate = 1.0
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], duplicate, switch)  ), getWellDuplicate(outputArtifacts[key], duplicate, switch), key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))   

            duplicate = 2.0
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], duplicate, switch)  ), getWellDuplicate(outputArtifacts[key], duplicate, switch), key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))

            duplicate = 3.0
            writer.writerow((getWell( getWellDuplicate(outputArtifacts[key], duplicate, switch)  ), getWellDuplicate(outputArtifacts[key], duplicate, switch), key, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))  

#    writer.writerow( ('84', 'G12', 'NTC' ,'' ,'' ,'Target 1','NTC','FAM','NFQ-MGB','', '') )
#    writer.writerow( ('96', 'H12', 'NTC' ,'' ,'' ,'Target 1','NTC','FAM','NFQ-MGB','', '') )
    f_out.close()

if __name__ == "__main__":
    main()
