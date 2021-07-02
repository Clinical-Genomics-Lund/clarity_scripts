import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
from xml.dom.minidom import parseString
import xlsxwriter
import CMDfunc
import CMDvar

HOSTNAME = ""
VERSION = ""
BASE_URI = ""
xrow = 0
xcol = 0

#Fixed pre-dilution (for example 5 for 1:5 dilution)
fixedDilution = 5.0
dilutionMargin = 0.9 * fixedDilution 

#Fragment size from Tapestation "Region 1 Average Size - bp" used when available. 

def visualization(f_out, analysis, limsID, sample) :
    global xrow
    global cell_format_2dec
    global cell_format_red
    global cell_format_yellow

    lcol = 0
    f_out.write_string(xrow, lcol, sample['labID'])
    lcol += 1
    f_out.write_string(xrow, lcol, limsID)
    lcol += 1
    f_out.write_string(xrow, lcol, sample['well'])
    lcol += 1
    try:
        f_out.write_number(xrow, lcol, sample['libraryConc'], cell_format_2dec)
    except:
        f_out.write_string(xrow, lcol, sample['libraryConc'])
    lcol += 1
    f_out.write_number(xrow, lcol, sample['dilution'])
    f_out.conditional_format(xrow,lcol,xrow,lcol,{'type':     'cell',
                                                  'criteria': 'equal to',
                                                  'value':    5,
                                                  'format':   cell_format_red})
    f_out.conditional_format(xrow,lcol,xrow,lcol,{'type':     'cell',
                                                  'criteria': 'equal to',
                                                  'value':    1,
                                                  'format':   cell_format_yellow})
    lcol += 1
    f_out.write_number(xrow, lcol, sample['volumePerSample'], cell_format_2dec)
    lcol += 1

    xrow += 1

def write_worklist(poolList) :
    worklistsPerPool = {}
    rowTranslation = {'A' : 1, 'B' : 2, 'C' : 3, 'D' : 4, 'E' : 5, 'F' : 6, 'G' : 7, 'H' : 8}
    poolOrder = []
    plateOrder = []

    # a dictonary containing a list of sampledict per pool
    for pool in poolList:
        containerPerPool = {}		# for each pool group by container
        poolOrder.append( pool )
        poolVolume = 0

        for sample in poolList[pool]:
            if poolVolume > 1200:
                poolOrder.append( pool + '_2' )
                poolVolume = 0

            if sample['containerName'] not in containerPerPool:
                containerSize = 96
                containerPerPool[ sample['containerName'] ] = ['']*containerSize

                if sample['containerName'] not in plateOrder:
                    if len(plateOrder) < 3:
                        plateOrder.append( sample['containerName'] )

                    else:
                        print("fail: only possible to pool a maximum of 3 96 well plates")
                        sys.exit(255)

            well = sample['well'].split(':')	# find the position depending on well
            pos = ( rowTranslation[ well[0] ] - 1 ) + ( int(well[1]) - 1 )*8

            containerStr = 'samplePlate[00%d]' % ( plateOrder.index( sample['containerName'] ) + 1 )

            containerPerPool[ sample['containerName'] ][ pos ] = ','.join([pool, sample['labID'], sample['limsID'], sample['containerName'], containerStr, ''.join(well), 'pool[00%d]' % ( poolOrder.index(pool) + 1 ), 'A1', str(sample['volumePerSample'])])

            poolVolume += sample[ "volumePerSample" ]

        # join all containers list to one list per pool
        for i in range( 0, len(plateOrder) ):
            container = plateOrder[i]

            if container in containerPerPool:
                if pool not in worklistsPerPool:
                    worklistsPerPool[pool] = containerPerPool[container]

                else:
                    worklistsPerPool[pool] = worklistsPerPool[pool] + containerPerPool[container]

    worklist = []

    # join pool lists to one list
    for pool in worklistsPerPool:
        for sample in worklistsPerPool[pool]:
            if sample != '':
                worklist.append(sample)

    return worklist, poolOrder, plateOrder

def normalization(f_out, data, poolURIs) : 
    global xrow
    global xcol
    poolList = {}

    for k in data.keys() :
        poolReadSum = 0
        lowestConc = 0
        minDilutionFactor = 0 
        sumDilutionFactors = 0
        sumOfng = 0
        minPoolVolume = 0

        f_out.write(xrow, xcol, "Analysis:")
        f_out.write(xrow, xcol+1, k)
        xrow += 1
        lcol = 0

        if "TWIST" not in k:
            for i in ['LabID', 'LimsID', 'WellLocation', 'LibraryConcentration(ng/ul)', 'Dilution', 'VolumePerSample(ul)'] :
                f_out.write(xrow, lcol, i)
                lcol += 1
        xrow += 1 

        for i in range(0,len(data[k])):
            s = data[k][i].keys()[0]
            poolReadSum += float(data[k][i][s]['readCount'])

            if lowestConc > 0 and data[k][i][s]['nM'] != '':
                if float(data[k][i][s]['nM']) < float(lowestConc) :
                    lowestConc = float(data[k][i][s]['nM'])

            elif lowestConc == 0 and data[k][i][s]['nM'] != '':
                lowestConc = float(data[k][i][s]['nM'])

        if lowestConc != 0:
            concCutOff = lowestConc * dilutionMargin

        for i in range(0,len(data[k])) :
            s = data[k][i].keys()[0]

            if "IDPT" in k:
                data[k][i][s]['dilution'] = 1.0

            else:
                data[k][i][s]['poolingFactor'] = float(data[k][i][s]['readCount']) / float(poolReadSum)

                if data[k][i][s]['nM'] > concCutOff :
                    data[k][i][s]['dilutionFactor'] = fixedDilution /float(data[k][i][s]['nM']) * float(data[k][i][s]['poolingFactor'])
                    data[k][i][s]['dilution'] = fixedDilution
                else: 
                    data[k][i][s]['dilutionFactor'] = 1.0/float(data[k][i][s]['nM']) * float(data[k][i][s]['poolingFactor'] )
                    data[k][i][s]['dilution'] = 1.0

                if minDilutionFactor == 0.0 :
                    minDilutionFactor = float(data[k][i][s]['dilutionFactor'])
                else : 
                    if data[k][i][s]['dilutionFactor'] < minDilutionFactor :
                        minDilutionFactor = float(data[k][i][s]['dilutionFactor'])

                sumDilutionFactors += float(data[k][i][s]['dilutionFactor'])

        #Find out minimum pool volume in order to calculate volume per sample
        if minDilutionFactor > 0:
            minPoolVolume = (2.0 * sumDilutionFactors) / minDilutionFactor

        if minPoolVolume > 0 and minPoolVolume < 10:
            poolVolume = 10
        elif minPoolVolume >= 10 :
            poolVolume = minPoolVolume
        else:
            poolVolume = 5 * len(data[k])
        
        #Calculate volume per sample
        for i in range(0,len(data[k])) :
            s = data[k][i].keys()[0]

            if "IDPT" in k:
                data[k][i][s]['volumePerSample'] = 5
            else:
                data[k][i][s]['volumePerSample'] = float(data[k][i][s]['dilutionFactor']) * (poolVolume / sumDilutionFactors)

            if data[k][i][s]['libraryConc'] != "":
                data[k][i][s]['ngPerSample'] = (float(data[k][i][s]['volumePerSample']) * float(data[k][i][s]['libraryConc']) ) / float(data[k][i][s]['dilution'])
                sumOfng += data[k][i][s]['ngPerSample']

            if "IDPT" in k :
                data[k][i][s].update( {'limsID' : s} )

                if k not in poolList:
                    poolList[k] = []

                poolList[k].append( data[k][i][s] )

            # Visualization to user
            if "TWIST" in k :
                f_out.write(xrow-1, 0, "Library pooling not required for TWIST pools", cell_format_blue)
                xrow += 2
            else:
                visualization(f_out, k, s, data[k][i][s])

        #Calculate expected pool concentration and update the pool
        if sumOfng == 0:
            expectedPoolConc = 0.0
        else:
            expectedPoolConc = sumOfng / poolVolume

        poolDOM = parseString(api.GET(poolURIs[k]))
        poolDOM = api.setUDF( poolDOM, "Pool volume (ul)", poolVolume )
        poolDOM = api.setUDF( poolDOM, "Expected Pool concentration (ng/ul)", expectedPoolConc )
        poolDOM = api.setUDF( poolDOM, "Total required read count", poolReadSum )
        r = api.PUT( poolDOM.toxml(), poolURIs[k])

        if "TWIST" not in k:
            f_out.write(xrow, 0, 'PoolVolume (ul): ' + str("{0:.2f}".format(poolVolume)).replace('.',','))
            xrow += 1
            f_out.write(xrow, 0, 'ExpectedPoolConcentration (ng/ul): ' + str("{0:.2f}".format(expectedPoolConc)).replace('.',','))
            xrow += 2

    return poolList

def getSampleData(stepURI, stepDOM, instrument, availableReads, availableReadsAdj, kit ) :
    poolURIs = {}
    sampleData = {}

    #Update step with reads info
    stepDOM = api.setUDF( stepDOM, "Available reads", availableReads )

    pURI = stepURI + "/pools"
    pURI = pURI.replace("processes", "steps")
    pDOM = parseString(api.GET(pURI))
    pools = pDOM.getElementsByTagName( "pool" )

    for pool in pools :
        totalReadSum = 0
        name = pool.getAttribute( "name" ).split("_")[0]

        #TWIST
        if "TWIST" in name:
            name_container = pool.getAttribute( "name" ).split("_")[0] + "-" + pool.getAttribute( "name" ).split("_")[1]

            #Save name and pool URI
            poolURIs[name_container] = pool.getAttribute( "output-uri" )
            sampleData[name_container] = []

            aURI = pool.getElementsByTagName( "input" )[0].getAttribute( "uri" )
            aDOM = parseString(api.GET( aURI ))
            limsID = aURI.split("/")[-1]
            labID = aDOM.getElementsByTagName( "name" )[0].firstChild.data
            well = aDOM.getElementsByTagName( "value" )[0].firstChild.data
            libraryConc = api.getUDF( aDOM, "Qubit concentration (ng/ul)" )
            if libraryConc == "" :
                libraryConc = api.getUDF( aDOM, "Concentration (ng/ul)" )
                if libraryConc == "":
                    print "All artifacts must have a value for concentration (ng/ul)"
                    sys.exit(255)
            if libraryConc < 0.3:
                print "Qubit concentration (ng/ul) must be higher than 0.3"
                sys.exit(255)

            #Go to submitted sample level for read count
            samples = aDOM.getElementsByTagName( "sample" )
            for s in samples :
                sDOM = parseString(api.GET( s.getAttribute( "uri" ) ))
                readCount = api.getUDF( sDOM, "Desired read count" )

                if readCount == "" :
                    print "Desired read count per sample must be specified at SubmittedSample level"
                    sys.exit(255)
                totalReadSum += float(readCount)


            readCount = totalReadSum

            #Convert ng/ul to nM
            fragmentLength = api.getUDF( aDOM, "Region 1 Average Size - bp" )
            if fragmentLength == "" :
                nM = float(libraryConc) * CMDvar.nMConversionFactor[name]
            else:
                nM = (float(libraryConc) * 1000000.0 ) / ( 660.0  * float(fragmentLength) )

            sDict = {}
            sDict[limsID ] = { 'labID' : labID,
                               'libraryConc' : float(libraryConc),
                               'nM' : float(nM),
                               'well' : well ,
                               'readCount' : float(readCount)}
            
            sampleData[name_container].append(sDict)

        elif "IDPT" in name:
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
		containerName = aDOM.getElementsByTagName( "container" )[0].getAttribute( "limsid" )
                
                libraryConc = api.getUDF( aDOM, "Qubit concentration (ng/ul)" )

                #Go to submitted sample level for read count
                sDOM = parseString(api.GET(sURI))
                readCount = api.getUDF( sDOM, "Desired read count" )

                if readCount == "" :
                    print "Desired read count per sample must be specified at SubmittedSample level"
                    sys.exit(255)

                totalReadSum += float(readCount)

                #Convert ng/ul to nM
                fragmentLength = api.getUDF( aDOM, "Region 1 Average Size - bp" )

                if libraryConc != "":
                    if fragmentLength == "" :
                        nM = float(libraryConc) * CMDvar.nMConversionFactor[name]
                    else:
                        try :
                            nM = (float(libraryConc) * 1000000.0 ) / ( 660.0  * float(fragmentLength) )
                        except :
                            print libraryConc, fragmentLength
                            sys.exit(255)
                else:
                    nM = ""

                sDict = {}
                sDict[limsID ] = { 'labID' : labID,
                                   'libraryConc' : libraryConc,
                                   'nM' : nM,
                                   'well' : well ,
                                   'readCount' : float(readCount),
                                   'containerName' : containerName}

                sampleData[name].append(sDict)

        else:
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

                #Go to submitted sample level for read count
                sDOM = parseString(api.GET(sURI))
                readCount = api.getUDF( sDOM, "Desired read count" )

                if readCount == "" :
                    print "Desired read count per sample must be specified at SubmittedSample level" 
                    sys.exit(255)

                #Correct readCount for Nextera QAML samples
                if name == "NexteraQAML" : 
                    if instrument == "NextSeq" :
                        readCount = ( (20.0/1300.0) * float(availableReadsAdj) ) / len(artifacts)
                    elif instrument == "MiniSeq" :
                        readCount = ( (10.0/500.0) * float(availableReadsAdj) ) / len(artifacts) 
                    elif kit == "NovaSeq SP 300" or kit == "NovaSeq S1 300":
                        readCount = ( (2.0/100.0) * float(availableReadsAdj) ) / len(artifacts)
                    elif kit == "NovaSeq S2 300" :
                        readCount = ( (3.0/150.0) * float(availableReadsAdj) ) / len(artifacts)
                    elif kit == "NovaSeq S4 300" :
                        readCount = ( (6.0/310.0) * float(availableReadsAdj) ) / len(artifacts)
                    
                    else:
                        print "Instrument name must be either MiniSeq or NextSeq" 
                        sys.exit(255)

                totalReadSum += float(readCount)

                #Convert ng/ul to nM
                fragmentLength = api.getUDF( aDOM, "Region 1 Average Size - bp" )
                if fragmentLength == "" :
                    nM = float(libraryConc) * CMDvar.nMConversionFactor[name]
                else:
                    try : 
                        nM = (float(libraryConc) * 1000000.0 ) / ( 660.0  * float(fragmentLength) )
                    except: 
                        print limsID , libraryConc
                        sys.exit(255)

                sDict = {}
                sDict[limsID ] = { 'labID' : labID, 
                                   'libraryConc' : float(libraryConc),
                                   'nM' : float(nM),
                                   'well' : well ,
                                   'readCount' : float(readCount)} 

                sampleData[name].append(sDict)

    return sampleData, poolURIs, totalReadSum, stepDOM

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
    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:k:x:l:w:")
    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-k':
            args[ "kit" ] = p
        elif o == '-x':
            args[ "phiX" ] = p
        elif o == '-l':
            args[ "outFile" ] = p
        elif o == '-w':
            args[ "worklist" ] = p

    setupGlobalsFromURI( args[ "stepURI" ] )
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )
    stepDOM = parseString( api.GET( args[ "stepURI" ] ) )
    kit = args[ "kit" ]
    availableReads = float( CMDvar.KitToReads[ kit ] )
    instrument =  kit.split(" ")[0]
    
    #Get PhiX spike-in and adjust available reads
    phiX = float(args[ "phiX" ])
    availableReadsAdj = (100.0 + phiX) * 0.01 * availableReads
    
    #Get necessary data per sample
    sampleData, poolURIs, totalReadSum, stepDOM = getSampleData(args[ "stepURI" ], stepDOM, instrument, availableReads, availableReadsAdj, kit)

    #Give warning if reads are missing 
    if totalReadSum > availableReadsAdj :
        print "WARNING! Too many samples. Number of reads missing: ", (totalReadSum - availableReadsAdj)
        sys.exit(255)

    #Calculate pooling factor, dilution factor, volume for pooling etc.
    f_outfile = xlsxwriter.Workbook(args[ "outFile" ] + '.xlsx')
    global cell_format_2dec
    global cell_format_red
    global cell_format_yellow
    global cell_format_blue
    cell_format_2dec = f_outfile.add_format()
    cell_format_2dec.set_num_format('0.00')
    cell_format_red = f_outfile.add_format({'bg_color':   '#FFC7CE',
                                            'font_color': '#9C0006'})
    cell_format_yellow = f_outfile.add_format({'bg_color':   '#FFEB9C',
                                               'font_color': '#9C6500'})
    cell_format_blue = f_outfile.add_format({'bg_color':   '#a7f0fc',
                                               'font_color': '#9C6500'})
    f_outsheet = f_outfile.add_worksheet()

    columns = (58, 27, 15, 25, 10, 20, 15, 10)
    for i in range(len(columns)):
        f_outsheet.set_column(i, i, columns[i])

    poolList = normalization(f_outsheet, sampleData, poolURIs)
    createWorklist = api.getUDF( stepDOM, "Worklist")

    if createWorklist == 'true' and poolList:
        orderedWorklist, poolOrder, plateOrder = write_worklist(poolList)

        stepDOM = api.setUDF( stepDOM, "Pool order", ', '.join(poolOrder) )
        stepDOM = api.setUDF( stepDOM, "Plate order", ', '.join(plateOrder) )

        with open( args[ "worklist" ] + '-poolingWorklist.csv', 'w') as worklist:
            worklist.write('Analysis,Sample name,clarity ID,plate name,scource plate,scource well,dest pool,dest well,volume\n')

            for line in orderedWorklist:
                worklist.write(line + '\n')

    r = api.PUT( stepDOM.toxml(), args[ "stepURI" ] )

    f_outfile.close()

if __name__ == "__main__":
    main()

