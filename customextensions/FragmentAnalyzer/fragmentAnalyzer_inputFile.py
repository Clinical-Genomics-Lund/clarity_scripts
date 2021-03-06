
import csv 
import glsfileutil
import glsapiutil
from xml.dom.minidom import parseString
from optparse import OptionParser



def limslogic():
    
    stepdetails = parseString( api.GET( options.stepURI + "/details" ) ) #GET the input output map
    resultMap = []

    #outputArtifacts = {}
    for iomap in stepdetails.getElementsByTagName( "input-output-map"):
        output = iomap.getElementsByTagName( "output" )[0]
        if output.getAttribute( "output-generation-type" ) == 'PerInput':
            oURI = output.getAttribute( "uri" )
            oDOM = parseString( api.GET( oURI ))
            #oLimsID = oDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
            smplName = oDOM.getElementsByTagName("name")[0].firstChild.data
            well = oDOM.getElementsByTagName( "value" )[0].firstChild.data
            well = well.replace(':' ,'', 1)
            wellPosition = placeNumber(well)
            lims_id=oDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
            resultMap.append([wellPosition,well,lims_id])
    #resultMap.append(['48','D12','Ladder'])
    #print(resultMap)
    return resultMap


def placeNumber(wellposition):

    letter = wellposition[0]
    number = int(wellposition[1:])
    letterDict = {'A' : 0, 'B' : 12, 'C' : 24, 'D' : 36, 'E' : 48, 'F' :60, 'G' :72, 'H' : 84  }
    well = letterDict[letter] + number
    return well

def writeOutput():
    #lines  = []
    lines = limslogic()
    print(lines)
    lines.append(['48','D12','Ladder'])
    print(lines)
    with open( options.outputfile +'_fragAnalyzer_samples.csv','w') as result_file:
        wr = csv.writer(result_file, dialect='excel')
        wr.writerows(lines)
        #wr.writerows(('48,D12,Ladder'))



def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')
    Parser.add_option('-f', "--outputfile", action='store', dest='outputfile')
    return Parser.parse_args()[0]

def main():
    global options
    options = setupArguments()
    global api
    api = glsapiutil.glsapiutil2()
    api.setURI( options.stepURI )
    api.setup( options.username, options.password )
    global FH
    FH = glsfileutil.fileHelper()
    FH.setAPIHandler( api )
    FH.setAPIAuthTokens( options.username, options.password )
    #limslogic()
    writeOutput()

if __name__ == "__main__":
    main()




