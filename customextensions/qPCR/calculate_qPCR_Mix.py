
import sys
import os
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
from optparse import OptionParser
#from xml.dom.minidom import parseString

api = None
options = None
num_samples = 0



def getAnalysis():
    placementDOM = parseString( api.GET( options.stepURI + "/placements" ) )
    containerURI = conURI = placementDOM.getElementsByTagName("selected-containers")[0].getElementsByTagName("container")[0].getAttribute("uri")
    cXML = api.GET( containerURI )
    cDOM = parseString( cXML )
    cType = cDOM.getElementsByTagName("type")[0].getAttribute( "uri" )
    
    num_samples = 0
    IOMaps = placementDOM.getElementsByTagName( "output-placement" )
    for IOMap in IOMaps:
        num_samples += 1 # to count the number of samples
        iURI = IOMap.getAttribute( "uri" )
        iXML = api.GET( iURI )
        iDOM = parseString( iXML )

        sURI = iDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
        sXML = api.GET( sURI )
        sDOM = parseString( sXML )
        if "WGS_qPCR" in sDOM.getElementsByTagName("name")[0].firstChild.data :
            analysis = "WGS" 
        else:
            analysis = api.getUDF( sDOM, "Analysis" )
    print(cType)
    
    if  ("WGS" in analysis) :
        flag =  'ON'
        n_samples = num_samples * 4
        if (cType == "http://localhost:9080/api/v2/containertypes/404"):
            n_strd = 14
            MasterMix = (n_samples + n_strd) * 12.4 * 1.2
            water =  (n_samples +n_strd) * 3.6 * 1.2
            red = 0
        elif (cType == "http://localhost:9080/api/v2/containertypes/454"):
            n_strd = 20
            MasterMix = (n_samples + n_strd) * 6.2 *1.2 
            water = 0
            red = 0
            #MasterMix = 11
        elif (cType == "http://localhost:9080/api/v2/containertypes/554"):
            n_strd = 20
            MasterMix = (n_samples + n_strd) * 6.2 *1.2
            water = 0
            red = 0

    else:
        flag = 'OFF'
        n_samples = num_samples * 2
        MasterMix = (n_samples + 10) * 5 * 1.2
        red = (n_samples + 10) * 0.5 * 1.2
        water = (n_samples + 10) * 2 * 1.2
    return MasterMix , water ,red , flag

def limslogic():
    mix , h2o , red, flag = getAnalysis()

    tokens = options.stepURI.split( "/" )
    BASE_URI = "/".join(tokens[0:5]) + "/"

    processURI = BASE_URI + "processes/" + tokens[-1]
    processDOM = parseString( api.GET(processURI) )
    if flag is 'ON':
        api.setUDF( processDOM, "KAPA SYBR Master mix (ul)", mix )
        api.setUDF( processDOM, "NF H2O (ul)", h2o )
    else:
        api.setUDF( processDOM, "TaqMan Master Mix - blue (ul)", mix )
        api.setUDF( processDOM, "NF H2O (ul)", h2o )
        api.setUDF( processDOM, "Quantification Assay - red (ul)", red )
    response = api.PUT( processDOM.toxml(), processURI )
    
def setupArguments():

    Parser = OptionParser()
    Parser.add_option('-u', "--username", action='store', dest='username')
    Parser.add_option('-p', "--password", action='store', dest='password')
    Parser.add_option('-s', "--stepURI", action='store', dest='stepURI')
    #Parser.add_option('-r', "--resultLUID", action='store', dest='resultLUID')

    return Parser.parse_args()[0]

def main():
    #MasterMix =  0
    #water = 0
    global options
    options = setupArguments()
    global api
    api = glsapiutil.glsapiutil2()
    api.setURI( options.stepURI )
    api.setup( options.username, options.password )


    #calculate_mix()
    #sys.exit(255)   
    #parseinputFile()
    #getAnalysis()
    limslogic()   

if __name__ == "__main__":
    main()
