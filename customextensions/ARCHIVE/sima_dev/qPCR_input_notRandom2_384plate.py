import sys
import csv
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString

HOSTNAME = 'https://clarity-test.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"
api = None


def getWells(well_pos):
    letterDict = {'A': 0, 'B' : 24, 'C' :48 , 'D' :72 , 'E' :96 , 'F' :120, 'G' :144, 'H' :168  ,'I':192, 'J':216, 'K':240, 'L':264, 'M':288, 'N':312, 'O':336, 'P':360}
    max_col = 24
    letter = well_pos.split(':')[0]
    pos= int(well_pos.split(':')[1])
    well =  letterDict[letter] + pos

    if pos != max_col - 1:
        well_dup1 = well + 1                                                                                                                                                                  
        well_dup2= well + 2                                                                                                                                                                    
        well_dup3= well + 3                                                                                                                                                                    
        well_pos_dup1= letter + str(pos+1)                                                                                                                                                  
        well_pos_dup2= letter + str(pos +2)                                                                                                                                                 
        well_pos_dup3= letter + str(pos+3) 
    else:
        well_dup1 = well + max_col
        well_dup2 = well + 1
        well_dup3 = well + max_col + 1
        for key, value in letterDict.iteritems():
            if value == letterDict[letter] + max_col:
                well_pos_dup1= key  + str(pos)
                well_pos_dup2= letter + str(pos +1)
                well_pos_dup3= key + str(pos + 1)
    return(well, well_dup1, well_dup2, well_dup3, well_pos_dup1, well_pos_dup2, well_pos_dup3)

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
    print(outputArtifacts)
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

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( "v2" )
    api.setup( args[ "username" ], args[ "password" ] )

    outputArtifacts = getOutputArtifacts()

    if len(outputArtifacts) > 88: 
        api.reportScriptStatus( stepURI, "ERROR", "Too many input samples. The maximum number of samples for this step is 88.")

    f_out = open(args[ "outputfile" ] + '.csv', 'w+')
    writer = csv.writer(f_out, delimiter=',', quotechar="\'")
#quoting=csv.QUOTE_NONE
    print("Writting the outputfile")
    f_out.write('[Sample Setup]'+ '\n')
    writer.writerow( ('Well', 'Well Position', 'Sample Name', 'Biogroup Name', 'Biogroup Color', 'Target Name', 'Task' , 'Reporter', 'Quencher', 'Quantity' ,'Comments') )
    if max_col == 24:
        writer.writerow( ('1', 'A1', 'ST1' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"20.0"','' ) ) 
        writer.writerow( ('25', 'B1', 'ST2' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"2.0"', '') )
        writer.writerow( ('49', 'C1', 'ST3' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.2"', '') )
        writer.writerow( ('73', 'D1', 'ST4' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.02"','' ))
        writer.writerow( ('97', 'E1', 'ST5' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.002"','' ))
        writer.writerow( ('121', 'F1', 'ST6' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.0002"','' ))
        writer.writerow( ('361', 'P1', 'NTC' ,'' ,'' ,'Target 1','NTC','SYBR','None','','' ) )

        writer.writerow( ('2', 'A2', 'ST1' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"20.0"','' ) )
        writer.writerow( ('26', 'B2', 'ST2' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"2.0"', '') )
        writer.writerow( ('50', 'C2', 'ST3' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.2"','' ) )
        writer.writerow( ('74', 'D2', 'ST4' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.02"','' ) )
        writer.writerow( ('98', 'E2', 'ST5' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.002"','' ))
        writer.writerow( ('122', 'F2', 'ST6' ,'' ,'' ,'Target 1','STANDARD','SYBR','None','"0.0002"','' ))
        writer.writerow( ('362', 'P2', 'NTC' ,'' ,'' ,'Target 1','NTC','SYBR','None','','' ) )
 
    elif max_col == 12:
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
            
    for  lims_id in outputArtifacts:
        well, well_dup1, well_dup2, well_dup3, well_pos_dup1, well_pos_dup2, well_pos_dup3 = getwells(outputArtifacts[lims_id])
        writer.writerow((well, outputArtifacts[lims_id],lims_id, '' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))
        writer.writerow((well_dup1, well_pos_dup1,lims_id,'' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))
        writer.writerow((well_dup2, well_pos_dup2,lims_id,'' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))
        writer.writerow((well_dup3, well_pos_dup3,lims_id,'' ,'' ,'Target 1','UNKNOWN','SYBR','None','', '' ))
    f_out.close()

if __name__ == "__main__":
    main()
