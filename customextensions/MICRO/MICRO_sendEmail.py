import sys
import getopt
import glsapiutil
import smtplib
from xml.dom.minidom import parseString
from email.mime.text import MIMEText
import subprocess

HOSTNAME = ""
VERSION = ""
BASE_URI = ""

api = None
SIMULATE = False

def updateProgressField(sURI) :

	sampleXML = api.GET( sURI )
	sampleDOM = parseString( sampleXML )
	
	api.setUDF( sampleDOM, 'Progress', 'Sequencing and Data Analysis Complete' )
	
	rXML = api.PUT( sampleDOM.toxml().encode('utf-8'), sURI )

def setupGlobalsFromURI( uri ):

	global HOSTNAME
	global VERSION
	global BASE_URI

	tokens = uri.split( "/" )
	HOSTNAME = "/".join(tokens[0:3])
	VERSION = tokens[4]
	BASE_URI = "/".join(tokens[0:5]) + "/"


def email_template1(eMailInfo ):
	body = []
	
	body.append( "This is an automated message from ClarityLIMS. Reports have been created for the following Microbiology samples:\n\n")
	body.append( "Lims ID\tSubmittedID\tQC info\n")

	for dict in eMailInfo:
		
		body.append( dict["limsID"] + "\t")
		body.append( dict["name"] + "\t")
		body.append( dict["QCinfo"] + "\t\n")
		
	body = "".join( body )
	return body


def send_email( email_SUBJECT_line, email_body, receiver ):

	cmd = """echo "{b}" | mailx -s "{s}" "{to}" 2>/dev/null""".format(b=email_body, s=email_SUBJECT_line, to=receiver)
	p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	output, errors = p.communicate()
	print errors,output

def main():

	global api
	global args

	args = {}

	opts, extraparams = getopt.getopt(sys.argv[1:], "s:u:p:")

	for o,p in opts:
		if o == '-s':
			args[ "stepURI" ] = p
		elif o == '-u':
			args[ "username" ] = p
		elif o == '-p':
			args[ "password" ] = p

	setupGlobalsFromURI( args[ "stepURI" ] )
	api = glsapiutil.glsapiutil2()
	api.setHostname( HOSTNAME )
	api.setVersion( VERSION )
	api.setup( args[ "username" ], args[ "password" ] )

	Inputs = []
	eMailMICRO = []

	#Get sample information
	stepURI = args[ "stepURI" ] + "/details"
	stepDOM = parseString(api.GET(stepURI))
	IOMaps = stepDOM.getElementsByTagName( "input-output-map" )
	for IOMap in IOMaps:
		if IOMap.getElementsByTagName( "output" )[0].getAttribute( "output-generation-type" ) == "PerInput":
			Inputs.append(IOMap.getElementsByTagName( "output" )[0].getAttribute( "uri" ))
		
	Inputs = set(Inputs)

	for i in Inputs :
		aDOM = parseString( api.GET(i))
		
		limsID = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )
		subSampleURI = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
		sDOM = parseString(api.GET(subSampleURI))
		updateProgressField(subSampleURI)

		analysis = api.getUDF( sDOM, "Analysis" )
		department = api.getUDF( sDOM, "Department" )
		classification = api.getUDF( sDOM, "Classification" )

		name = sDOM.getElementsByTagName( "name" )[0].firstChild.data
		QCinfo = api.getUDF( aDOM, "Sample Classification" )
		QCinfo = QCinfo.encode('latin')
		if "Ej Godk" in QCinfo : 
			QCinfo = "failed"
		elif "Uppdatering/Ny data analys" in QCinfo: 
			QCinfo = "reanalyzed sample"
		else: 
			QCinfo = "passed"
		
		
		if (( "Micro" in analysis ) and ( department == "Klinisk Mikrobiologi" ) and ( classification == "Rutinprov" ) ) :

			eMailMICRO.append({"name" : name, "limsID" : limsID , "QCinfo" : QCinfo , "department" : department}) 

	email_SUBJECT_line = 'ClarityLIMS notification'

	if len(eMailMICRO) >=1 :
		email_body = email_template1(eMailMICRO)
		send_email( email_SUBJECT_line, email_body, 'Maryem.Salim@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Anna.SoderlundStrand@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Maria.Liljeheden@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Carolina.Lundberg@skane.se' ) 
		send_email( email_SUBJECT_line, email_body, 'Yuk.Ting.Siu@skane.se' ) 
		send_email( email_SUBJECT_line, email_body, 'Jonas.Bjorkman@skane.se' ) 
		
		

if __name__ == "__main__":
	main()
