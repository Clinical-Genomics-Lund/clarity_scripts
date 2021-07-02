import sys
import getopt
import glsapiutil3
import smtplib
from xml.dom.minidom import parseString
from email.mime.text import MIMEText
import subprocess

api = None

def email_template1(eMailInfo ):
	body = []
	
	body.append( "This is an automated message from ClarityLIMS. Please see OncomineFocus initial Qubit concentrations below:\n\n")
	body.append( "Submitted ID_Lims ID\tDV200\tStatus\tAnalysis\n")


	for dict in eMailInfo:
		body.append( dict["name"] + "_" + dict["limsID"] + "\t")
		body.append( dict["DV200"] + "\t")
		body.append( dict["qc"] + "\t")
		body.append( dict["analysis"] + "\n")
		
	body = "".join( body )
	return body

def send_email( email_SUBJECT_line, email_body, receiver ):

	cmd = """echo "{b}" | mailx -s "{s}" "{to}" 2>/dev/null""".format(b=email_body, s=email_SUBJECT_line, to=receiver)
	p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	output, errors = p.communicate()
	print(errors,output)

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

	api = glsapiutil3.glsapiutil3()
	api.setup( username=args[ "username" ], password=args[ "password" ] , sourceURI =args[ "stepURI" ])

	Inputs = []
	eMailONC = []

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
		
		DV200 = api.getUDF( aDOM, "Region 1 % of Total" )
		qc = aDOM.getElementsByTagName( "qc-flag" )[0].firstChild.data
		limsID = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "limsid" )

		subSampleURI = aDOM.getElementsByTagName( "sample" )[0].getAttribute( "uri" )
		sDOM = parseString(api.GET(subSampleURI))

		analysis = api.getUDF( sDOM, "Analysis" )
		department = api.getUDF( sDOM, "Department" )
		
		name = sDOM.getElementsByTagName( "name" )[0].firstChild.data
		
		if department == "Klinisk Patologi" and "Oncomine Focus" in analysis:
			eMailONC.append({"name" : name, "limsID" : limsID, "DV200" : DV200, "qc" : qc , "analysis" : analysis}) 

	email_SUBJECT_line = 'ClarityLIMS notification'

	if len(eMailONC) >=1 :
		email_body = email_template1(eMailONC)
		send_email( email_SUBJECT_line, email_body, 'Maryem.Salim@skane.se' )
#		send_email( email_SUBJECT_line, email_body, 'Maj.Westman@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Morten.Grauslund@skane.se' )
#		send_email( email_SUBJECT_line, email_body, 'Annica.Bjornback@skane.se' )
#		send_email( email_SUBJECT_line, email_body, 'Malgorzata.Tomaszewska@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Per.Leveen@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Li.Zhou@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Marta.Lukasiewicz@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Emilie.Andreasen@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Heike.Kotarsky@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Klara.Leonhard@skane.se' )
		send_email( email_SUBJECT_line, email_body, 'Asa.S.Hakansson@skane.se' )
		

if __name__ == "__main__":
	main()
