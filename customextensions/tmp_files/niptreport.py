#!python
# -*- coding: latin-1 -*-
import sys
import getopt
import glsapiutil
import xml.dom.minidom
import os
import re
import string
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
import urllib2
import csv
import time
import random
import pprint

import sys

reload(sys)
sys.setdefaultencoding('utf8')

HOSTNAME = 'https://mtapp046.lund.skane.se'
VERSION = "v2"
BASE_URI = HOSTNAME + "/api/" + VERSION + "/"

DEBUG = False
api = None
args = None



html_escape_table = {
        u'&': "&amp;",
        u'"': "&quot;",
        u"'": "&apos;",
        u'>': "&gt;",
        u'<': "&lt;",
        u'å': "&aring;",
        u'ä': "&auml;",
        u'ö': "&ouml;",
        u'Å': "&Aring;",
        u'Ä': "&Auml;",
        u'Ö': "&Ouml;"
        }

def html_escape(text):
    return "".join(html_escape_table.get(c,c) for c in text)


# Get UDFs from a dom into a dict
def get_UDFs(dom):
    udf_data = {}
    elements = dom.getElementsByTagName( "udf:field" )
    for udf in elements:
        udf_data[ udf.getAttribute("name") ] = udf.firstChild.data

    return udf_data


# Return LU UDFs and correspnding sample UDFs in a dict
def get_data(dom):
    lu_udfs = {}
    sample_data = {}

    # Get UDF data for LU artifact
    lu_udfs = get_UDFs(dom)

    artifact_id = dom.getAttribute("limsid")
    

    # Get sample ID and URI
    sample = dom.getElementsByTagName("sample")
    sample_lims_id  = sample[0].getAttribute("limsid")
    sample_lims_uri = sample[0].getAttribute("uri")

            
    # Fetch sample data
    sample_xml = api.GET( sample_lims_uri )
    if sample_xml:
        sample_dom = parseString(sample_xml)

        sample_data = get_UDFs( sample_dom )
        sample_data["genesis_id"] = sample_dom.getElementsByTagName("name")[0].firstChild.data


    # Get technician name from parent process
    parent_process_uri = dom.getElementsByTagName("parent-process")[0].getAttribute("uri")
    parent_process_xml = api.GET( parent_process_uri )
    if parent_process_xml:
        parent_process_dom = parseString(parent_process_xml)
        technician = parent_process_dom.getElementsByTagName("technician")
        sample_data["technician_name"] = technician[0].getElementsByTagName("first-name")[0].firstChild.data + " " + technician[0].getElementsByTagName("last-name")[0].firstChild.data




    sample_data["ID"] = sample_lims_id
    #sample_data["Comment_old"] = lu_udfs.get("Comment", "")
    sample_data["Freetext"] = lu_udfs.get("NIPT report - free text", "")
    sample_data["Comment"] = lu_udfs.get("NIPT report - comment", "")
    sample_data["SampleClassification"] = lu_udfs.get("Sample Classification", "")
    sample_data["FailAction"] = lu_udfs.get("Sample Failed - Action", "")
    sample_data["LUID"] = artifact_id
    return sample_data
                                                                                                                                            


def complete_file( artifactluid_offile,outfile ):    ### finds the file LUID from artifact LUID of the file

    fileLUID = " "
    artif_URI = BASE_URI + "artifacts/" + artifactluid_offile
    print artif_URI
    artXML = api.GET(artif_URI)      #GET artifact XML
    artDOM = parseString( artXML )
    
    Nodes = artDOM.getElementsByTagName( "file:file" )
    fileLUID = Nodes[0].getAttribute( "limsid" )
    
    file_URI = BASE_URI + "files/" + fileLUID + "/download"
    fileGET = api.GET(file_URI) ##retrieves the file
    with open(outfile, 'wb') as fd:
        fd.write(fileGET)


def nl_list(elems):
    if len(elems) == 1:
        return elems[0]
    else:
        st = ""
        for idx, elem in enumerate(elems):
            st = st + str(elem)
            if( idx == len(elems) - 2 ):
                st = st + " eller "
            elif( idx < len(elems) - 2 ):
                st = st + ", "
        return st
                                                            


def generate_html( data, niptdata ):
    

    with open(niptdata) as csvfile:
        reader = csv.DictReader( csvfile, delimiter="\t" )
        for row in reader:
            # Get LIMS-ID, should be everything before the first "_" or "-".
            id_parts = re.split( "[-_]", row["Sample ID"] )
            lims_id = id_parts[0]

            if lims_id == data["ID"]:
                sentence = ""
                result_summary = ""
                fail_text = ""
                positive = []
                negative = []
                nac = []
                low_fetal = False
                for chrom in ["13", "18", "21"]:
                    if row['Chr'+str(chrom)+" call"] == "Positive":
                        positive.append(chrom)
                    if row['Chr'+str(chrom)+" call"] == "Negative":
                        negative.append(chrom)
                    if row['Chr'+str(chrom)+" call"] == "Not automatically called":
                        nac.append(chrom)
                    if row['Chr'+str(chrom)+" call"] == "Low fetal fraction":
                        low_fetal = True

                # If "godkänt" prov, check that FailAction was not selected.
                if( "Godk" in data["SampleClassification"] and "Ej Godk" not in data["SampleClassification"] ):
                    if( data["FailAction"] != "- Standard -" ): 
                        print( '"' + data["FailAction"] + '"' + u" får ej väljas vid " + '"' + data["SampleClassification"] + '"')
                        sys.exit(255)

                # If "Ej Godkänt", check that FailAction WAS selected. 
                else:
                    if( data["FailAction"] == "- Standard -" ):
                        print( u'Välj något i "Sample Failed - Action"' )
                        sys.exit(255)
                    # Dont generate report for these options
                    elif( data["FailAction"] == "Ny DNA-extraktion" or data["FailAction"] == "Ny bibliotekspreparation" or data["FailAction"] == "Omsekvensering av bibliotek" ):
                        return("NO_REPORT", "NO_REPORT")
                    # Save FailAction-text
                    else:
                        fail_text = data["FailAction"]+"."

                # If free text was selected
                if( data["Comment"] == "Endast fri text" ):
                    if "Freetext" in data and len(data["Freetext"]) > 0:
                        sentence = data["Freetext"]
                        result_summary = "TEXT"
                    else:
                        print('Fyll i en text')
                        sys.exit(255)

                # Automatically generated 
                elif data["Comment"] == "Automatiskt genererad":

                    if (len(negative) + len(nac)) == 3:
                        sentence = u"Ingen f&ouml;rh&ouml;jd sannolikhet f&ouml;r trisomi "+nl_list(negative)+" har p&aring;visats i provet."
                        result_summary = "NEG"

                    if row['Chr13 call'] == "Positive":
                        sentence = u"F&ouml;rh&ouml;jd sannolikhet f&ouml;r trisomi 13 har p&aring;visats i provet. Invasivt prov rekommenderas."
                        result_summary = "POS13 "
                    if row['Chr18 call'] == "Positive":
                        sentence = u"F&ouml;rh&ouml;jd sannolikhet f&ouml;r trisomi 18 har p&aring;visats i provet. Invasivt prov rekommenderas."
                        result_summary = "POS18 "
                    if row['Chr21 call'] == "Positive":
                        sentence = u"F&ouml;rh&ouml;jd sannolikhet f&ouml;r trisomi 21 har p&aring;visats i provet. Invasivt prov rekommenderas."
                        result_summary = "POS21 "
                    if row['Chr13 call'] == "Low fetal fraction" or row['Chr18 call'] == "Low fetal fraction" or row['Chr21 call'] == "Low fetal fraction":
                        sentence = u"Patientens prov har analyserats och bed&ouml;mts som inkonklusivt pga f&ouml;r l&aring;g fetalfraktion."
                        result_summary = "LFF "
                    if row['Fetal fraction'] == "Insufficient sample coverage":
                        sentence = u"Patientens prov har analyserats och bed&ouml;mts som inkonklusivt."
                        result_summary = "INSUFF_COV "
                    if row['Chr13 call'] == "Sample correlation is too low" or row['Chr18 call'] == "Sample correlation is too low" or row['Chr21 call'] == "Sample correlation is too low":
                        sentence = u"Patientens prov har analyserats och bed&ouml;mts som inkonklusivt."
                        result_summary = "LFF "

                    if len(nac):
                        sentence = sentence + u" Trisomistatus f&ouml;r kromosom "+nl_list(nac)+" kunde ej best&auml;mmas."
                        result_summary = result_summary + ( " ".join( [ "N"+x for x in nac ] ) )

                    if len(fail_text) > 0:
                        sentence = sentence +" "+ fail_text

                    if "Freetext" in data and len(data["Freetext"]) > 0:
                        sentence = sentence + " " + data["Freetext"]

                # Pre-written comment selected
                else:
                    if len(fail_text) > 0:
                        print u'"NIPT report - comment" måste vara "Automatiskt genererad" vid "'+fail_text+'"'
                        sys.exit(255)
                    sentence = data["Comment"] + " " + data.get("Freetext", "")
                    if "trisomi 13." in data["Comment"]:
                        result_summary = "POS13 "
                    if "trisomi 18." in data["Comment"]:
                        result_summary = "POS18 "
                    if "trisomi 21." in data["Comment"]:
                        result_summary = "POS21 "
                    if "sannolikhet f" in data["Comment"]:
                        result_summary = "NEG "

                    if len(nac):
                        result_summary = result_summary + ( " ".join( [ "N"+x for x in nac ] ) )


                f1 = open( data["ID"]+".html", 'w+' )

                for chr_call in ["Chr13 call", "Chr18 call", "Chr21 call"]:
                    if row[chr_call] == "Negative":
                        row[chr_call] = "<span class='neg'>negativ</span>"
                    elif row[chr_call] == "Positive":
                        row[chr_call] = "<span class='pos'>positiv</span>"
                    elif row[chr_call] == "Low fetal fraction":
                        row[chr_call] = "L&aring;g fetalfraktion"

                f1.write(
u"""<!doctype html><html>
<head>
  <title>NIPT report</title>
  <link rel="stylesheet" type="text/css" href="/home/petter/niptreport/report.css">
  <meta charset="UTF-8">
</head>

<body>

<div class="page">

<img class="logo" src="/home/petter/niptreport/rslogo.png">
<span class="report_header">Analysrapport, NIPT - """+data.get('genesis_id',"")+u"""</span>

<div class="report_div">
  <table class="report_general">
    <tr>
      <td class="top_report_key">Patientnamn</td><td class="top_report_val">"""+ html_escape( data.get('Patient Name', "SAKNAS") ) +u"""</td>
    </tr>                                                                                                                                        
    <tr>
      <td class="top_report_key">Personnummer</td><td class="top_report_val">""" + data.get('Personal Identity Number', "SAKNAS") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Prov-ID</td><td class="top_report_val">""" +data.get('genesis_id',"SAKNAS") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Ankomstdatum</td><td class="top_report_val">""" + data.get("Date of arrival", "SAKNAS") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Provtyp</td><td class="top_report_val"> Cellfritt cirkulerande DNA fr&aring;n blod</td>
    </tr>
    <tr>
      <td class="top_report_key">Rapportdatum</td><td class="top_report_val">""" + time.strftime("%x") +u"""</td>
    </tr>
    <tr>
      <td class="top_report_key">Analysmetod</td><td class="top_report_val">Clarigo, non-invasive prenatal test (NIPT)</td>
    </tr>
    <tr>
      <td class="top_report_key">Analys genomf&ouml;rd av</td><td class="top_report_val">Centrum f&ouml;r Molekyl&auml;r diagnostik (CMD) och Klinisk genetik</td>
    </tr>
    <tr>
      <td class="top_report_key">Rapport genererad av</td><td class="top_report_val">""" + data.get("technician_name", "SAKNAS") +u""" </td>
    </tr>
    <tr>
      <td class="top_report_key">Rapport-ID</td><td class="top_report_val">""" + data['genesis_id'] +"."+str(random.randrange(1000000,9999999)) +u"""</td>
    </tr>
  </table>
</div>


<span class="report_header">Testresultat</span>

<div class="results_summary">""" + sentence + u"""</div>

<span class="report_text">Fetalfraktion: """ + row["Fetal fraction"] + u"""</span><br>
<table class="report_general">
  <tr>
    <th class="top_report"></th>
    <th class="top_report">Resultat</th>
    <th class="top_report">Evidensv&auml;rde</th>
    <th class="top_report">Z-v&auml;rde</th>
  </tr>
  <tr>
    <td class="top_report_key">Kromosom 13</td><td class="top_report_val">"""+row["Chr13 call"] +u"""</td><td class="top_report_val">"""+row["Chr13 evidence"] +u"""</td><td class="top_report_val">"""+row["Chr13 Z-score"] +u"""</td> 
  </tr>
  <tr>
    <td class="top_report_key">Kromosom 18</td><td class="top_report_val">"""+row["Chr18 call"] +u"""</td><td class="top_report_val">"""+row["Chr18 evidence"] +u"""</td><td class="top_report_val">"""+row["Chr18 Z-score"] +u"""</td> 
  </tr>
  <tr>
    <td class="top_report_key">Kromosom 21</td><td class="top_report_val">"""+row["Chr21 call"] +u"""</td><td class="top_report_val">"""+row["Chr21 evidence"] +u"""</td><td class="top_report_val">"""+row["Chr21 Z-score"] +u"""</td> 
  </tr>
</table>   </tr>

<span class="report_header">Metodbeskrivning</span>
<span class="report_text">Analysen &auml;r en CE-IVD-m&auml;rkt screening av fetal aneuploidi-status f&ouml;r kromosom 13, 18 och 21 i cellfritt DNA (cfDNA) preparerat fr&aring;n maternalt blod. En riktad amplifiering av cfDNA f&ouml;ljt av massivt parallell sekvensering (MPS, &auml;ven kallat NGS) har utf&ouml;rts. Ett analyssvar kan inte ges f&ouml;re graviditetsvecka 8, vid maternella kromosomavvikelser, vid multipla graviditeter, graviditet genom &auml;ggdonation, placental mosaicism, partiell fetal aneuploidi, "vanishing twins" eller fetalfraktion under 4%.</span>
</table>
</style>

</div>

</body>
</html>""")
                csvfile.close()
                f1.close()
                return (data["ID"]+".html", result_summary)


	
def main():

    global api
    global args
    global batchDOM

    args = {}
    fileLUID = " "
    opts, extraparams = getopt.getopt(sys.argv[1:], "a:b:u:p:f:")

    for o,p in opts:
        if o == '-a':
            args[ "artifactLUID" ] = p
        elif o == '-u':
            args[ "username" ] = p
        elif o == '-p':
            args[ "password" ] = p
        elif o == '-f':
            args[ "outputfileLUIDs" ] = p
        elif o == '-b':
            args[ "clarigofile" ] = p

    outputfileLUIDs = args[ "outputfileLUIDs" ].split(" ")

    api = glsapiutil.glsapiutil2()
    api.setHostname( HOSTNAME )
    api.setVersion( VERSION )
    api.setup( args[ "username" ], args[ "password" ] )


    # WHY?
    complete_file( args[ "clarigofile" ],"clarigodata.txt" )

    os.system("cp clarigodata.txt /all")


    output_artifacts = parseString( api.getArtifacts(outputfileLUIDs) )

    f = open( "/all/nipt_luid.xml", 'w+' )

    for dom in output_artifacts.getElementsByTagName("art:artifact"):

        # Get sample data
        data = get_data( dom )
        LUID = data["LUID"]


        # Generate PDF
        f.write(pprint.pformat(data)+"\n\n")
        (html_fn, summary) = generate_html( data, "clarigodata.txt" )

        if html_fn != "NO_REPORT": 
            os.system("cp "+html_fn+" /all")
            pdf_fn = LUID + "." + data["genesis_id"] + ".pdf"
            os.system("scp " + html_fn + " petter@10.0.224.63:/home/petter/niptreport/")
            
            os.system("ssh petter@10.0.224.63 '/home/petter/anaconda/bin/weasyprint /home/petter/niptreport/"+html_fn+" /home/petter/niptreport/"+LUID+".pdf && scp /home/petter/niptreport/"+LUID+".pdf glsai@mtapp046.lund.skane.se:/all'")

            os.system("mv /all/" + LUID + ".pdf " + pdf_fn)
        # Set result UDF
        api.setUDF( dom, "NIPT test results", summary )
        os.system("rm /all/"+os.path.basename(html_fn))

        print ":P"

    f.close()
    # Update step artifact
    r = api.POST( output_artifacts.toxml().encode('utf-8'), BASE_URI + "artifacts/batch/update/" )
    
if __name__ == "__main__":
    main()
