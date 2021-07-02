import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import xlsxwriter

HOSTNAME = ""
VERSION = ""
BASE_URI = ""
xrow = 0
xcol = 0

nMConversionFactor = { "TwistMyeloid" : 2.47, 
                       "TwistClinicalWES" : 2.47, 
                       "TwistHereditarySolid" : 2.47, 
                       "TwistLymphoma" : 2.47}
#nM convertion factor = (conc * 1000000) / (660 * 525) 

def visualization(f_out, limsID , sample) :
    global xrow
    global cell_format_2dec
    global cell_format_red
#    global cell_format_yellow

    lcol = 0
    f_out.write_string(xrow, lcol, sample['labID'])
    lcol += 1
    f_out.write_string(xrow, lcol, limsID)
    lcol += 1
    f_out.write_string(xrow, lcol, sample['well'])
    lcol += 1
    f_out.write_number(xrow, lcol, sample['libraryConc'], cell_format_2dec)
    lcol += 1
    f_out.write_number(xrow, lcol, sample['volPerSample'], cell_format_red)
    xrow += 1

def normalization(f_out, data, poolURIs, poolReadDistr) : 
    global xrow
    global xcol

    ngPerPool = { 8 : 187.5 , 
                  7 : 214.3 , 
                  6 : 250 , 
                  5 : 300 , 
                  4 : 375 ,
                  3 : 500 , 
                  2 : 500, 
                  1 : 500 }

    xls_sampledata = {}
    xls_pooldata = {}
    for pool in sorted(data.keys()) :
        xls_sampledata[pool] = []
        xls_pooldata[pool] = {}

        f_out.write(xrow, xcol, "Pool name:")
        f_out.write(xrow, xcol+1, pool)
        xrow += 1
        lcol = 0

        for i in ['LabID', 'LimsID', 'WellLocation', 'LibraryConcentration(ng/ul)', 'VolumePerSample(ul)'] :
            f_out.write(xrow, lcol, i)
            lcol += 1
        xrow += 1 
        
        numberOfSamples = len(data[pool] )
        totalReadCount = 0

        if poolReadDistr[pool] == "Equal" :
            totalVolumePool = 0.0
            totalMassPerPool = 1500.0
            if numberOfSamples == 2 :
                totalMassPerPool = 1000.0
            elif numberOfSamples == 1 :
                totalMassPerPool = 500.0

            ngPerSample = ngPerPool[numberOfSamples] 
            for count, item in enumerate(data[pool], start=0) :
                volPerSample = ngPerSample / data[pool][count][item.keys()[0]]['libraryConc']
                totalVolumePool += volPerSample
                data[pool][count][item.keys()[0]]['volPerSample'] = volPerSample
                #f_out, limsID , sample
                visualization(f_out, item.keys()[0] , data[pool][count][item.keys()[0]] )
                xls_sampledata[pool].append( data[pool][count][item.keys()[0]] )

            f_out.write(xrow, 0, 'TotalMassPerPool(ng): ' + str("{0:.2f}".format(totalMassPerPool)).replace('.',',')) 
            xrow += 1
            f_out.write(xrow, 0, 'TotalVolume (ul): ' + str("{0:.2f}".format(totalVolumePool)).replace('.',',')) 
            xls_pooldata[pool] = { 'TotalMassPerPool(ng)' : totalMassPerPool, 
                               'TotalVolume (ul)' : totalVolumePool}
            xrow += 3
    
        else: 
            totalVolumePool = 0.0
            #ng per sample must be modified by read count
            totalMassPerPool = 1500.0
            if numberOfSamples == 2 :
                totalMassPerPool = 1000.0

            for count, item in enumerate(data[pool], start=0) :
                totalReadCount += data[pool][count][item.keys()[0]]['readCount']
            
            for count, item in enumerate(data[pool], start=0) :
                fractionReadCount = data[pool][count][item.keys()[0]]['readCount'] / totalReadCount
                fractionOfPool = totalMassPerPool * fractionReadCount
                volPerSample = fractionOfPool / data[pool][count][item.keys()[0]]['libraryConc']
                totalVolumePool += volPerSample
                data[pool][count][item.keys()[0]]['volPerSample'] = volPerSample
                #f_out, limsID , sample
                visualization(f_out, item.keys()[0] , data[pool][count][item.keys()[0]])
                xls_sampledata[pool].append( data[pool][count][item.keys()[0]] )

            f_out.write(xrow, 0, 'TotalMassPerPool(ng): ' + str("{0:.2f}".format(totalMassPerPool)).replace('.',','))
            xrow += 1
            f_out.write(xrow, 0, 'TotalVolume (ul): ' + str("{0:.2f}".format(totalVolumePool)).replace('.',','))
            xrow += 2
            xls_pooldata[pool] = { 'TotalMassPerPool(ng)' : totalMassPerPool,
                                   'TotalVolume (ul)' : totalVolumePool}
        

def getSampleData(stepURI) :
    poolURIs = {}
    poolReadDistr = {}
    sampleData = {}

    pURI = stepURI + "/pools"
    pURI = pURI.replace("processes", "steps")
    pDOM = parseString(api.GET(pURI))
    pools = pDOM.getElementsByTagName( "pool" )

    for pool in pools :
        readCountList = []
        poolAnalysis = "" 

        name = pool.getAttribute( "name" )

        #Save name and pool URI 
        poolURIs[name] = pool.getAttribute( "output-uri" )
        sampleData[name] = []

        #Loop over pool contents 
        artifacts = pool.getElementsByTagName( "input" )
        for a in artifacts :
            aDOM = parseString(api.GET( a.getAttribute( "uri" ) ))
            limsID = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
            sURI = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
            labID = aDOM.getElementsByTagName( "name" )[0].firstChild.data
            well = aDOM.getElementsByTagName( "value" )[0].firstChild.data
            libraryConc = api.getUDF( aDOM, "Qubit concentration (ng/ul)" )

            if libraryConc == "" :
                libraryConc = api.getUDF( aDOM, "Concentration (ng/ul)" )
                if libraryConc == "" :
                    print "All artifacts must have a value for concentration (ng/ul)" 
                    sys.exit(255)
            if libraryConc < 0.3:
                print "Qubit concentration (ng/ul) must be higher than 0.3"
                sys.exit(255)

            #Check that all samples require same capture pool 
            sDOM = parseString(api.GET(sURI))
            analysis = api.getUDF( sDOM, "Analysis" )
            analysis = analysis.split(" ")[-1]

            if poolAnalysis == "" :
                poolAnalysis = analysis
            else: 
                if analysis != poolAnalysis : 
                    print "All samples in a pool must have same value for 'Analysis'" 
                    sys.exit(255)

            #Go to submitted sample level for read count
            readCount = api.getUDF( sDOM, "Desired read count" )
            
            if readCount == "" :
                print "Desired read count per sample must be specified at SubmittedSample level" 
                sys.exit(255)
                
            readCountList.append(readCount)

            #Convert ng/ul to nM
            fragmentLength = api.getUDF( aDOM, "Region 1 Average Size - bp" )
            if fragmentLength == "" :
                nM = float(libraryConc) * nMConversionFactor[name.split("_")[0]]
            else:
                nM = (float(libraryConc) * 1000000.0 ) / ( 660.0  * float(fragmentLength) )

            sDict = {}
            sDict[limsID ] = { 'labID' : labID, 
                               'libraryConc' : float(libraryConc),
                               'nM' : float(nM),
                               'well' : well ,
                               'readCount' : float(readCount)} 

            sampleData[name].append(sDict)

        #Check if all samples require the same read count 
        result = False
        result = all(elem == readCountList[0] for elem in readCountList)

        if result :
            poolReadDistr[name] = "Equal"
        else:
            poolReadDistr[name] = "Not equal"

    return sampleData, poolURIs, poolReadDistr

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
    api = None    
    api = glsapiutil.glsapiutil2()

    args = {}
    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:l:")
    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-l':
            args[ "outFile" ] = p

    setupGlobalsFromURI( args[ "stepURI" ] )
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )
    
    #Get necessary data per sample
    sampleData, poolURIs, poolReadDistr = getSampleData(args[ "stepURI" ])

    #Calculate pooling factor, dilution factor, volume for pooling etc.
    f_outfile = xlsxwriter.Workbook(args[ "outFile" ] + '.xlsx')
    global cell_format_2dec
    global cell_format_red
#    global cell_format_yellow
    cell_format_2dec = f_outfile.add_format()
    cell_format_2dec.set_num_format('0.00')
    cell_format_red = f_outfile.add_format({'bg_color':   '#FFC7CE',
                                            'font_color': '#9C0006'})
    cell_format_red.set_num_format('0.00')
#    cell_format_yellow = f_outfile.add_format({'bg_color':   '#FFEB9C',
#                                               'font_color': '#9C6500'})
    f_outsheet = f_outfile.add_worksheet()
    columns = (37, 25, 15, 25, 20)
    for i in range(len(columns)):
        f_outsheet.set_column(i, i, columns[i])
    
    normalization(f_outsheet, sampleData, poolURIs, poolReadDistr)

    f_outfile.close()

if __name__ == "__main__":
    main()
