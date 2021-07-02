import sys
import re
import getopt
import xml.dom.minidom
import glsapiutil
import platform
from xml.dom.minidom import parseString
from email.mime.text import MIMEText
import subprocess

HOSTNAME = platform.node() # get the system hostname
HOSTNAME = "https://" + HOSTNAME
VERSION = "v2"
CACHE = {}
api = None

def getObject( URI ):

    global CACHE

    if URI not in CACHE.keys():
        xml = api.getResourceByURI( URI )
        CACHE[ URI ] = xml

    return CACHE[ URI ]    

def setUDF( self, DOM, udfname, udfvalue ):
    newDOM = DOM

    ##if the node already exists, delete it
    elements = newDOM.getElementsByTagName( "udf:field" )
    for element in elements:
        if element.getAttribute( "name" ) == udfname:
            newDOM.childNodes[0].removeChild( element )

    #now add the new UDF node
    newNode = newDOM.createElement( "udf:field" )
    newNode.setAttribute( "name", udfname )
    txt = newDOM.createTextNode( udfvalue )
    newNode.appendChild( txt )
    newDOM.childNodes[0].appendChild( newNode )
    return newDOM

def email_template(sampleID, limsID ):
    body = []

    body.append( "This is an automated message from ClarityLIMS. The following RNA sample did not pass sequencing QC:\n\n")
    body.append( "Submitted ID\tLims ID\n")
    body.append( sampleID + "\t")
    body.append( limsID + "\t")
        
    body = "".join( body )
    return body

def send_email( email_SUBJECT_line, email_body, receiver ):

    cmd = """echo "{b}" | mailx -s "{s}" "{to}" 2>/dev/null""".format(b=email_body, s=email_SUBJECT_line, to=receiver)
    p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, errors = p.communicate()
    print errors,output

def checkFileAttachment(oURI) :
    global fail
    oXML = getObject( oURI )
    oDOM = parseString( oXML )

    #Get the Classification
    Classification = api.getUDF( oDOM, "Sample Classification" ).encode('UTF-8')

    if "Rutinprov - Godk" in Classification :
        #Get the file node
        if not oDOM.getElementsByTagName( "file:file" ):
            stepURI = args[ "stepURI" ]
            stepURI = re.sub("http://localhost:9080", HOSTNAME, stepURI)
            fail += 1
            api.reportScriptStatus( stepURI, "ERROR", "Result file must be uploaded")
        else :
            file_uri = oDOM.getElementsByTagName("file:file")[0].getAttribute( "uri" ) 
            fileDOM = parseString ( getObject(file_uri) ) 
            file_name = (fileDOM.getElementsByTagName( "original-location" )[0].firstChild.data).split(".")[-1]
            if file_name != "pdf" :
                stepURI = args[ "stepURI" ]
                stepURI = re.sub("http://localhost:9080", HOSTNAME, stepURI)
                api.reportScriptStatus( stepURI, "ERROR", "The Result file must be a PDF file" )

    elif "Rutinprov - Ej Godk" in Classification :
        if oDOM.getElementsByTagName( "name" )[0].firstChild.data[-3:] == "RNA" :
            sampleID = oDOM.getElementsByTagName( "name" )[0].firstChild.data
            limsID = oDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
            email_body = email_template(sampleID, limsID)
            email_SUBJECT_line = 'ClarityLIMS notification'
            send_email( email_SUBJECT_line, email_body, 'Maryem.Salim@skane.se' )
            send_email( email_SUBJECT_line, email_body, 'Maj.Westman@skane.se' )
            send_email( email_SUBJECT_line, email_body, 'Morten.Grauslund@skane.se' )
            send_email( email_SUBJECT_line, email_body, 'Per.Leveen@skane.se' )
            send_email( email_SUBJECT_line, email_body, 'Heike.Kotarsky@skane.se' )
                

def setProgressUDF(oURI) :

    oXML = getObject(oURI )
    oDOM = parseString( oXML )
    #Get Sample URI
    Nodes = oDOM.getElementsByTagName( "sample" )
    sampleURI = Nodes[0].getAttribute( "uri" )
    sampleXML = getObject( sampleURI )
    sampleDOM = parseString( sampleXML )

    api.setUDF( sampleDOM, 'Progress', 'Sequencing and Data Analysis Complete' )

    rXML = api.updateObject( sampleDOM.toxml().encode('utf-8'), sampleURI )                                

def getInputSamples():

    detailsURI = args[ "stepURI" ] + "/details"
    detailsURI = re.sub("http://localhost:9080", HOSTNAME, detailsURI)
    detailsXML = api.getResourceByURI( detailsURI )
    detailsDOM = parseString( detailsXML )

    IOMaps = detailsDOM.getElementsByTagName( "input-output-map" )
    for IOMap in IOMaps:
        Nodes = IOMap.getElementsByTagName( "output" )
        if Nodes[0].getAttribute( "output-generation-type" ) == "PerInput" :
            oURI = Nodes[0].getAttribute( "uri" )
            InputSamples.append(oURI)
    
    return InputSamples

def main():

    global api
    global args
    global InputSamples
    global fail

    args = {}
    InputSamples = []
    fail = 0

    opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

    for o,p in opts:
        if o == '-s':
            args[ "stepURI" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p

    api = glsapiutil.glsapiutil()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )

    InputSamples = getInputSamples()
    #First check file attachment 
    for oURI in InputSamples :
        checkFileAttachment(oURI)
    #Then update the progress field if everything went well with the attachment check
    if fail == 0 :
        for oURI in InputSamples :
            setProgressUDF(oURI)

if __name__ == "__main__":
    main()
