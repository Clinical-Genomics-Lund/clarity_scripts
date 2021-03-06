import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil3
from xml.dom.minidom import parseString
import datetime
import os
from subprocess import call


now = datetime.datetime.now()
api = None

def printLabel(pool, date):
    filename = '/all/' + pool + '.zpl'
    f = open(filename, 'w+')
    analysis = pool.split("_")[0]
    containerID = pool.split("_")[1]

    f.write('^XA\n^BY3.0,1,25\n^FO1,0\n^BQN,2,2\n^FDMM,_' + pool + '^FS\n^FO110,30^ADN,10,5^FD' + analysis + '^FS\n^FO110,50^ADN,10,5^FD' + containerID + '^FS\n^FO110,70^ADN,10,5^FD' + date + '^FS\n^XZ')
    f.close()
    call( ['lp','-d','ZebraLabCMD','-o','raw',filename])
    os.remove(filename)

def getInputSamples():
    tmpList = []
    OutputSamples = []
    detailsURI = args[ "stepURI" ] + "/details"
    detailsXML = api.GET( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" :
            oURI = Nodes[0].getAttribute( "uri" )
            if oURI not in tmpList:
                tmpList.append(oURI)
    
    for URI in tmpList:
        XML = api.GET( URI )
        DOM = parseString( XML )
        #Get pool name
        name = DOM.getElementsByTagName( "name" )[0].firstChild.data
        
        OutputSamples.append(name)
    return OutputSamples

def main():

    global api
    global args

    args = {}
    SampleInfoList = []

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil3.glsapiutil3()
    api.setup( username=args[ "username" ], password=args[ "password" ] , sourceURI =args[ "stepURI" ])

    OutputSamples = getInputSamples()
    #Get the date
    date = now.strftime("%Y-%m-%d")

    for pool in sorted(OutputSamples) :
        printLabel(pool, date)   

if __name__ == "__main__":
    main()
