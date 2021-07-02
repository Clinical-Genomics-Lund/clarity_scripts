#-*- coding: utf-8 -*-
import re
import sys

def getTWISTinfo(planID, DOM, Name, sLimsID, sUDFs):
    
    SampleID = sLimsID + "_" + planID

    DiagnosisDict = { "Hematologisk neoplasi" : "AML" ,
                      "KLL" : "KLL",
                      "MPN" : "MPN" ,
                      "Annat" : "other",
                      "Hematologisk neoplasi efter transplantation" : "AlloSCT" }

    if "GMSMyeloid" in sUDFs["Analysis"] or "Ovarial" in sUDFs["Analysis"] or "GMSLymphoma" in sUDFs["Analysis"]:
        #Get Tumor/Normal
        if "normal" in sUDFs["Sample Type"] or "Normal" in sUDFs["Sample Type"]:
            SampleType = "N"
        elif "malignitet" in sUDFs["Sample Type"] or "Tum" in sUDFs["Sample Type"]:
            SampleType = "T"
        else:
            print "The Sample Type field of the TWIST samples must contain either Normal or Tumor"
            sys.exit(255)

    #Get Tissue (FFPE or X) 
    Tissue = "X"
    if "Tissue" in sUDFs.keys():
        if sUDFs["Tissue"] == "FFPE":
            Tissue = "FFPE"
            
    #Get Diagnosis
    try:
        Diagnosis = DiagnosisDict[sUDFs["Diagnosis"]]
    except :
        Diagnosis = "other"
                
    #Get paired/unpaired information
    try :
        PairedSample = sUDFs["Paired Sample Name"]
        paired = "paired"
        if SampleType == "T" :
            groupID = Name
        elif SampleType == "N" :
            groupID = PairedSample
    except:
        paired = "unpaired"
        PairedSample = "X"
        groupID = Name

    #Get analysis
    analysis = sUDFs["Analysis"]
    if "GMSMyeloid" in analysis:
        analysis = analysis.split(" ")[-1]
        analysis = analysis.replace(".", "-")

        #Combine sampleProjDescription
        items = (analysis, 
                 Name, 
                 paired, 
                 PairedSample, 
                 groupID, 
                 SampleType, 
                 Diagnosis, 
                 Tissue)
        SampleProj_Description = "_".join(items)

    elif "Onkogenetik" in analysis: 
        if "screening" in analysis:
            analysisType = "screening"
        elif "prediktiv" in analysis :
            analysisType = "predictive"
        else: 
            print "Screening/predictive must be indicated for sample " , Name 
            sys.exit(255)

        #Get gender 
        if "Sex" in sUDFs:
            if sUDFs["Sex"] == "Man":
                sex = "M"
            elif sUDFs["Sex"] == "Kvinna":
                sex = "F"
            elif sUDFs["Sex"] == u"Okänt" :
                sex = "U"
        else :
            print "Man, Kvinna or Okant must be indicated for sample ", Name 
            sys.exit(255)

        #Get genelist 
        if "Gene list" in sUDFs :
            
            geneLists = { u"Ärftlig bröstcancer" : "arftlig-brostcancer",
                          u"Ärftlig äggstockscancer" : "arftlig-aggstockscancer" ,
                          u"Lynch syndrom / PPAP" : "lynch-syndromPPAP", 
                          u"Lynch syndrom" : "lynch-syndromPPAP", 
                          u"Kolonpolypos" : "kolonpolypos" , 
                          u"Ärftligt malignt melanom" : "arftlig-maligntmelanom" , 
                          u"Anpassad analys" : "anpassad-analys", 
                          u"Annat" : "other", 
                          "Brca35" : "Brca35"
                          }

            #More than one gene list
            if "," in sUDFs["Gene list"] :
                tmp = []
                Genelist = sUDFs["Gene list"].split(", ")
                for Glist in Genelist :
                    try :
                        tmp.append( geneLists[ Glist ] )
                    except:
                        print "Check gene list field for sample " , Name , " . If more than one gene lists are used, please use ',' as seperator."
                        sys.exit(255)
                        
                tmp = ("+").join(tmp)
                genelist =  tmp
                        
            #Only one gene list
            else :
                try:
                    genelist = geneLists[ sUDFs["Gene list"] ]
                except:
                    print "Check gene list field for sample " , Name , " . If more than one gene lists are used, please use ',' as seperator."
                    sys.exit(255)
        else: 
            genelist = "other"

        panel = analysis.split(" ")[-1]
        version = panel[-4:]
        version = version.replace(".", "-")
        analysis = "onco" + version

        #Combine sampleProjDescription  
        items = ( analysis, 
                  Name, 
                  "proband", 
                  groupID, 
                  "X", 
                  "X", 
                  sex, 
                  "affected", 
                  genelist, 
                  Tissue, 
                  analysisType)  
        SampleProj_Description = "_".join(items)

    elif "Ovarial" in analysis: 
        panel = analysis.split(" ")[-1]
        version = panel[-4:]
        version = version.replace(".", "-")
        #analysis = "ovarian" + version changed 2021-01-15
        analysis = "PARPinhib" + version

        #Combine sampleProjDescription
        items = (analysis, 
                 Name, 
                 paired, 
                 PairedSample, 
                 groupID, 
                 SampleType, 
                 Diagnosis, 
                 Tissue)
        SampleProj_Description = "_".join(items)

    elif "clinicalWES" in analysis : 
        panel = analysis.split(" ")[-1]
        version = panel[-4:]
        version = version.replace(".", "-")
        analysis = "clinicalwes" + version

        #Combine sampleProjDescription
        items = (analysis, 
                 Name)
        SampleProj_Description = "_".join(items)

    elif "SciLifePanCancer" in analysis :
        #panel = analysis.split(" ")[-1]
        version = analysis[-4:]
        version = version.replace(".", "-")
        analysis = "scilifepancancer" + version
        
        #Combine sampleProjDescription
        items = (analysis, 
                 Name,
                 Tissue)
        SampleProj_Description = "_".join(items)

    elif analysis in ["GMSSolidTumorv2.0", "GMSSolidTumorv1.0"] :
        #panel = analysis.split(" ")[-1]
        version = analysis[-4:]
        version = version.replace(".", "-")
        analysis = "gmssolidtumor" + version
        
        #Combine sampleProjDescription
        items = (analysis,
                 Name, 
                 Tissue)
        SampleProj_Description = "_".join(items)

    elif "GMSLymphoma" in analysis:
        analysis = analysis.split(" ")[-1]
        analysis = analysis.replace(".", "-")
        analysis = analysis.lower()

        #Combine sampleProjDescription
        items = (analysis, 
                 Name, 
                 paired,
                 PairedSample,
                 groupID,
                 SampleType,
                 Diagnosis,
                 Tissue)
        SampleProj_Description = "_".join(items)

    elif "MODY" in analysis:
        analysis = analysis.replace(".", "-")
        analysis = analysis.replace("_", "-")
        analysis = analysis.lower()

        items = (analysis,
                 Name,
                 paired,
                 PairedSample,
                 groupID,
                 'X',
                 Diagnosis,
                 Tissue)
        SampleProj_Description = "_".join(items)        
        
    return SampleID, SampleProj_Description
            

def getMICROinfo(planID, DOM, Name, sLimsID, sUDFs):

    SampleID = sLimsID + "_" + planID

    required = ["Species", 
                "Department"
                ] 

    for item in required: 
        if not sUDFs[item] : 
            print item , " must be indicated for microbiology samples" 
            sys.exit(255)

    species = sUDFs["Species"] 
    department = sUDFs["Department"]

    if "CTG" in department:
        assay = "microbiology-CTG"
    else: 
        assay = "microbiology"

    items = (assay, 
             Name,
             species ) 
    SampleProj_Description = "_".join(items)

    return SampleID, SampleProj_Description


def getNIPTinfo(planID, DOM, Name, sLimsID, sUDFs):

    SampleID = sLimsID + "_" + Name

    assay = 'nipt'

    items = (assay, Name)
    SampleProj_Description = "_".join(items)

    return SampleID, SampleProj_Description


def getSARSinfo(planID, DOM, Name, sLimsID, sUDFs):
    #SampleID = sLimsID + "_" + planID
    SampleID = Name

    required = ["Department"]

    for item in required:
        if not sUDFs[item] :
            print item , " must be indicated for Sars-CoV-2 samples"
            sys.exit(255)

    assay = "sarscov2"

    items = (assay,
             Name)
    #SampleProj_Description = "_".join(items)
    SampleProj_Description = "sarscov2"

    return SampleID, SampleProj_Description



def getRNASEQinfo(planID, DOM, Name, sLimsID, sUDFs):

    SampleID = sLimsID + "_" + planID

    diagnosisDict = { "Annat" : "other", 
                      u"Solid tumör" : "solidtumor", 
                      "AML/MDS/MPN" : "AML-MDS-MPN", 
                      }
    #fusioncatcher
    if "TruSeq Stranded mRNA - Fusion" in sUDFs["Analysis"] :
        assay = "rnaseq-fusion"
        
        if "Diagnosis" in sUDFs:
            try: 
                Diagnosis = diagnosisDict[ sUDFs["Diagnosis"] ] 
            except : 
                Diagnosis = sUDFs["Diagnosis"]
        else: 
            Diagnosis = "other" 
        type = Diagnosis

    #bladderclassifier
    elif "TruSeq Stranded mRNA - Bladder" in sUDFs["Analysis"] :
        assay = "rnaseq-bladder" 
        type = "rnaseq-bladder"

    #SCAN-B (RNA expression breast)
    elif "TruSeq Stranded mRNA - Expression - Breast" in sUDFs["Analysis"] :
        try: 
            scanB = sUDFs["SCAN-B ID"]
        except: 
            print "SCANB-ID missing for sample " + Name 
            sys.exit(255)
        assay = "rnaseq-exp-breast"
        type = scanB

    #alignment and STAR
    else:
        assay = "rnaseq"
        type = "rnaseq"
    items = (assay, 
             Name, 
             type)
    SampleProj_Description = "_".join(items)

    return SampleID, SampleProj_Description




def getMYELOIDinfo(planID, DOM, Name, sLimsID, sUDFs):

    DiagnosisDict = { "Hematologisk neoplasi" : "AML" ,
                      "KLL" : "KLL",
                      "MPN" : "MPN" , 
                      "Annat" : "Annat", 
                      "Hematologisk neoplasi efter transplantation" : "AlloSCT" }

    #Get Tumor/Normal
    if "normal" in sUDFs["Sample Type"] :
        SampleType = "N"
    elif "malignitet" in sUDFs["Sample Type"] :
        SampleType = "T"
    else:
        print "The Sample Type field of the Myeloid samples must contain either Vavnadsbiopsi normal or Hematologisk malignitet"
        sys.exit(255)

    #Get Diagnosis
    try:
        Diagnosis = DiagnosisDict[sUDFs["Diagnosis"]]
    except :
        print "Sample Diagnosis must be either Hematologisk neoplasi, KLL, MPN, Annat or Hematologisk neoplasi efter transplantation for the Myeloid samples"
        sys.exit(255)

    #Get paired/unpaired information
    if "Myeloisk Panel - Parad" in sUDFs["Analysis"] :
        Analysis = "paired"
        try :
            PairedSample = sUDFs["Paired Sample Name"]
        except: 
            print "Paired samples must have a value for 'Paired Sample Name'" 
            sys.exit(255)
    elif "Myeloisk Panel - Oparad" in sUDFs["Analysis"] :
        Analysis = "unpaired"
        PairedSample = "X"
    else :
        print "Analysis must be either 'Myeloisk Panel - Parad' or 'Myeloisk Panel - Oparad'"
        sys.exit(255)

    #Get Panel from appended workflow-specific container identifier
    #CAN2 == Nextera, LNP == TruSight Myeloid
    tokens = Name.split("_")
    if tokens[1] == 'CAN2' :
        SampleID = sLimsID + "_N_" + planID
        if PairedSample == "X":
            #Unpaired
            SampleProj_Description = "myeloid_N" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + Diagnosis
        else:
            #Paired
            SampleProj_Description = "myeloid_N" + tokens[0] + "_" + Analysis + "_N" + PairedSample + "_" + SampleType + "_X"

    elif tokens[1] == 'LNP' :
        SampleID = sLimsID + "_" + planID
        if PairedSample == "X":
            #Unpaired 
            SampleProj_Description = "myeloid_" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + Diagnosis
        else: 
            #Paired
            SampleProj_Description = "myeloid_" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_X"
    else :
        print "The workflow identifiers 'CAN2' or 'LNP' must be appended to the Library name"
        sys.exit(255)

    return SampleID, SampleProj_Description



                
def getEXOMEinfo(planID, DOM, Name, sLimsID, sUDFs):

    SampleID = sLimsID + "_" + planID

    #Sample Project and Description Field examples
    #Trio : exome_3901-15_3901-15_proband_M_affected_pediatrics
    #Single : exome_3213-16_X_X_M_affected_ahus
    #Tumor : exome-tumor_8776-17_paired_8775-17_T_F_neuroblastom
    #BRCA unpaired:
    #BRCA paired:
    
    DiagnosisDict = { "Pediatrik" : "pediatrics" ,
                      "Annat" : "other" , 
                      "aHUS" : "ahus" , 
                      "complement" : "complement" , 
                      "HAE" : "HAE" }

    if "Diagnosis" in sUDFs:
        try : 
            Application = DiagnosisDict[sUDFs["Diagnosis"]] 
        except: 
            print "The diagnosis field must contain either aHUS, complement, Annat or Pediatrik"
            sys.exit(255)

    else:
        if "Tumor" in sUDFs["Analysis"]:
            Application = "other"
        elif "BRCA" in sUDFs["Analysis"] :
            Application = "BRCA"
        elif "CTG" in sUDFs["Analysis"] :
            Application = ""

        elif "Gene list" in sUDFs :

            geneLists = { "Kanalopati" : "Kanalopati" ,
                          "Komplex kardiologi" : "Komplex-kardiologi" ,
                          "Kardiomyopati" : "Kardiomyopati", 
                          "RASopati" : "RASopati" ,
                          "PAH HHT CM-AVM" : "PAH-HHT-CM-AVM" ,
                          "Anpassad" : "Anpassad" , 
                          "Stroke" : "Stroke" , # by Viktor
                          "CMT/Neuropati" : "cmt-neuropati", 
                          "Ataxi" : "ataxi", 
                          "Osteogenesis imperfecta" : "Osteogenesis-imperfecta",
                          u"Bindvävssjukdomar" : "Bindvavssjukdomar",
                          u"Hörselnedsättning" : "Horselnedsattning" ,
                          u"Hereditär Spastisk Parapares" : "hsp" 
                          }

            #More than one gene list
            if "," in sUDFs["Gene list"] :
                tmp = []
                Genelist = sUDFs["Gene list"].split(", ")
                for Glist in Genelist :
                        try : 
                            tmp.append( geneLists[ Glist ] )
                        except:
                            print "The gene list field must contain one of the following option: Kanalopati,Bindv:avssjukdomar,Komplex kardiologi,Kardiomyopati,RASopati, H:orselneds:attning, Anpassad, PAH HHT CM-AVM, CMT/Neuropati, Stroke, Hereditar Spastisk Parapares or Ataxi. If more than one gene lists are used, please use ',' as seperator."
                            sys.exit(255)

                tmp = ("+").join(tmp)
                Application =  tmp

            #Only one gene list
            else :
                    try:
                        Application = geneLists[ sUDFs["Gene list"] ]
                    except:
                        print "The gene list field must contain one of the following option: Kanalopati,Bindv:avssjukdomar,Komplex kardiologi,Kardiomyopati,RASopati, H:orselneds:attning, Anpassad, PAH HHT CM-AVM, CMT/Neuropati, Stroke, Hereditar Spastisk Parapares or Ataxi."
                        sys.exit(255)


    if ( (sUDFs["Analysis"] == "SureSelectXTHS - Trio Exome") or (sUDFs["Analysis"] == "SureSelectXTHS - Single Exome") or (sUDFs["Analysis"] == "SureSelectXTHS - Paired Tumor Exome")or (sUDFs["Analysis"] == "SureSelectXTHS - Unpaired Tumor Exome") ):

        #For these samples, gender must be indicated
        if "Sex" in sUDFs:
            if sUDFs["Sex"] == "Man":
                sex = "M"
            elif sUDFs["Sex"] == "Kvinna":
                sex = "F"
            elif sUDFs["Sex"] == u"Okänt" :
                sex = "U"
        else :
            print "Man, Kvinna or Okant must be indicated for the SureSelect XTHS samples"
            sys.exit(255)


        #Check the Trio samples
        if sUDFs["Analysis"] == "SureSelectXTHS - Trio Exome" :
        
            if "Sample Type" in sUDFs:
                if sUDFs["Sample Type"] == "Frisk":
                    Type = "unaffected"
                elif sUDFs["Sample Type"] == "Sjuk" :
                    Type = "affected"
                else:
                    print "The Sample Type field must contain either Sjuk or Frisk"
                    sys.exit(255)
            else :
                print "The Sample Type field must contain either Sjuk or Frisk for trio samples"
                sys.exit(255)


            if "Pedigree" in sUDFs:
                pedigree = sUDFs["Pedigree"]
                if pedigree == "Mamma":
                    pedigree = "mother"
                elif pedigree == "Pappa":
                    pedigree = "father"
                elif pedigree == "Proband" :
                    pedigree = "proband"
                elif pedigree == "Annat":
                    pedigree = "other"
                else :
                    print "The pedigree must be either Mamma, Pappa, Proband or Annat for the SureSelect XTHS samples"
                    sys.exit(255)
            else :
                print "The pedigree must be either Mamma, Pappa, Proband or Annat for the SureSelect XTHS samples"
                sys.exit(255)
            items = ("exome", 
                     Name,
                     sUDFs["FamilyID"],
                     pedigree,
                     sex,
                     Type,
                     Application)
            SampleProj_Description = "_".join(items)

        #Single samples
        elif sUDFs["Analysis"] == "SureSelectXTHS - Single Exome" :
            items = ("exome", 
                     Name,
                     "X", 
                     "X",
                     sex,
                     "affected", 
                     Application)
            SampleProj_Description = "_".join(items)

        #Tumor Samples
        elif "Tumor" in sUDFs["Analysis"]:
            #Get paired/unpaired information
            if "Paired Tumor Exome" in sUDFs["Analysis"] :
                Analysis = "paired"
                try: 
                    PairedSample = sUDFs["Paired Sample Name"]
                except:
                    print "Paired Sample Name must be indicated for paired tumor samples" 
                    sys.exit(255)
            else :
                Analysis = "unpaired"
                PairedSample = "X"

            #Get Tumor/Normal
            try : 
                SampleType = sUDFs["Sample Type"][:1]
            except:
                print "The Sample Type field of the SureSelect Tumor samples must contain either 'Normalprov' or 'Tumorprov'"
                sys.exit(255)

            #Get department for Coyote
            department = sUDFs["Department"].replace(" ", "") 

            items = ("exome-tumor",
                     Name,
                     Analysis,
                     PairedSample,
                     SampleType,
                     sex,
                     Application, 
                     department)
            SampleProj_Description = "_".join(items)

    elif ("BRCA" in sUDFs["Analysis"] ) :
        #BRCA samples

        #Get Tumor/Normal
        try :
            SampleType = sUDFs["Sample Type"][:1]
        except:
            print "The Sample Type field of the BRCA samples must contain either 'Normalprov' or 'Tumorprov'"
            sys.exit(255)

        #Get paired/unpaired information
        if "Paired BRCA" in sUDFs["Analysis"] :
            Analysis = "paired"
            try:
                PairedSample = sUDFs["Paired Sample Name"]

            except:
                print "Paired Sample Name must be indicated for paired BRCA samples"
                sys.exit(255)

        else :
            Analysis = "unpaired"
            PairedSample = "X"


        #Get tissue
        Tissue = "X"
        if "Tissue" in sUDFs.keys():
            if sUDFs["Tissue"] == "FFPE":
                Tissue = "FFPE"
        
        items = ("brca", 
                 Name, 
                 Analysis,
                 PairedSample,
                 SampleType,
                 Application,
                 Tissue)
        SampleProj_Description = "_".join(items)

    elif ("CTG" in sUDFs["Analysis"] ) :
        #CTG exome samples
        SampleProj_Description = "_".join("exome-ctg", 
                                          Name )

    else:
        print "Trio, Single, Tumor, CTG or BRCA must be indicated in the analysis field for the SureSelect XTHS samples"
        sys.exit(255)

    return SampleID, SampleProj_Description



def gethumanWGSinfo(planID, DOM, Name, sLimsID, sUDFs ):

    SampleID = sLimsID + "_" + planID

    #Sample Project and Description Field examples
    #Family :wgs-family_4224-12_proband_4224-12_4225-12_4226-12_M_affected_other__highest
    #Single : wgs-single_3529-19_proband_3529-19_X_X_M_affected_Genelist_aHus_highest
    #Tumor : wgs-somatic_9091-19_unpaired_X_T_M_other_KliniskGenetik

    changeDict = { "Kvinna" : "F",
                   "Man" : "M",
                   u"Okänt" : "U" ,
                   "Sjuk" : "affected",
                   "Frisk" : "unaffected",
                   "Pediatrik" : "pediatrics" ,
                   "Annat" : "other" ,
                   "aHUS" : "ahus" ,
                   "HAE" : "HAE" ,
                   "complement" : "complement",
                   "Kanalopati" : "Kanalopati" ,
                   "Komplex kardiologi" : "Komplex-kardiologi" ,
                   "Kardiomyopati" : "Kardiomyopati",
                   "RASopati" : "RASopati" ,
                   "PAH HHT CM-AVM" : "PAH-HHT-CM-AVM" ,
                   "Anpassad" : "Anpassad" ,
                   u"Stroke" : "Stroke" ,
                   "CMT/Neuropati" : "cmt-neuropati",
                   "Ataxi" : "ataxi",
                   "Osteogenesis imperfecta" : "Osteogenesis-imperfecta",
                   u"Bindvävssjukdomar" : "Bindvavssjukdomar",
                   u"Hörselnedsättning" : "Horselnedsattning" ,
                   u"Hereditär Spastisk Parapares" : "hsp",
                   "Neurodegeneration" : "Neurodegeneration" ,
                   u"Medfött hjärtfel" : "Medfott-hjartfel",
                   "Hematologisk malignitet" : "hemato",
                   u"Solid tumör" : "solid",
                   u"Ofullständig trio" : "Ofullstandig-trio",
                   u"PanelApp Pediatric Cardiomyopathy" : "PanelAppPediatricCardiomyopathy", 
                   "Optikusneuropati" : "optikusneuropati", 
                   u"Blödning och trombocytsjukdomar" : "blodning-och-trombocytsjukdomar",
                   "Trombofili" : "trombofili" , 
                   "Anemi" : "anemi" , 
                   u"Cytopeni (ej Fanconis anemi)" : "cytopeni-ej-fanconis-anemi" , 
                   "Fanconis anemi eller Blooms syndrom" : "fanconi-anemi-eller-blooms-syndrom",
                   u"Primär immunbrist" : "primar-immunbrist",
                   "KIT" : "kit"
                   }

    #Set priority
    urgent = ""
    if "Urgent" in sUDFs:
        if sUDFs["Urgent"] == "Ja" :
            urgent = "highest"

    #Get somatic or constitutional:
    if "family" in sUDFs["Analysis"]:

        #Get reference genome version (hg19 until ~2020-03)
        referenceGenome = sUDFs["Reference genome"]
        if referenceGenome == "" :
            print "Reference genome must be indicated"
            sys.exit(255)
        else:
            if referenceGenome == "hg19" :
                assay = "wgs"
            if referenceGenome == "hg38" :
                assay = "wgs-hg38"
                    

        try:
            pedigree = sUDFs["Pedigree"]
            familyID = sUDFs["FamilyID"]
            sex = changeDict[ sUDFs["Sex"] ]
            status = changeDict[ sUDFs["Sample Type"] ]
        except :
            print "Pedigree, FamilyID, Sex and Sample Type must be indicated for WGS family samples"
            sys.exit(255)
            
        if "Proband" in sUDFs["Pedigree"] :
            pedigree = "proband"
        else:
            pedigree = "relative"
                
        try:
            motherID = sUDFs["MotherID"]
        except :
            motherID = "X"
            
        try:
            fatherID = sUDFs["FatherID"]
        except:
            fatherID = "X"

        geneList = "other" #not relevant for family samples
        application = "" #not relevant for family samples
            
        if "Topup read count" in sUDFs :
            assay = assay + "-topup"

        items = (assay, 
                 Name, 
                 pedigree, 
                 familyID, 
                 motherID, 
                 fatherID, 
                 sex, 
                 status, 
                 geneList, 
                 application,
                 urgent
                 )
        SampleProj_Description = "_".join(items) 

    elif "single" in sUDFs["Analysis"] :
        #Get reference genome version (hg19 until ~2020-03)
        referenceGenome = sUDFs["Reference genome"]
        if referenceGenome == "" :
            print "Reference genome must be indicated"
            sys.exit(255)
        else:
            if referenceGenome == "hg19" :
                assay = "wgs"
            if referenceGenome == "hg38" :
                assay = "wgs-hg38"
                    
        pedigree = "proband"
        familyID = Name
        motherID = "X"
        fatherID = "X"
        status = "affected"

        try :
            sex = changeDict[ sUDFs["Sex"] ]
        except:
            print "Sex must be indicated for WGS single samples"
            sys.exit(255)

        if "Gene list" in sUDFs.keys() :
            try:
                geneList = changeDict[sUDFs["Gene list"] ]
                
            except:
                if "," in sUDFs["Gene list"] :
                    tmp = []
                    Genelist = sUDFs["Gene list"].split(", ")
                    
                    for Glist in Genelist :
                        try :
                            tmp.append( changeDict[ Glist ] )
                        except:
                            print "The gene list field is not recognized"
                            sys.exit(255)
                            
                    tmp = ("+").join(tmp)
                    geneList =  tmp
            application = ""

        elif sUDFs["Diagnosis"] :
            geneList = "other"
            try:
                application = changeDict[sUDFs["Diagnosis"] ]
            except:
                print "The diagnosis field is not recognized"
                sys.exit(255)
        else:
            application = "other"
            
        if "Topup read count" in sUDFs :
            assay = assay + "-topup"

        items = (assay, 
                 Name, 
                 pedigree, 
                 familyID, 
                 motherID, 
                 fatherID, 
                 sex, 
                 status, 
                 geneList, 
                 application, 
                 urgent) 

        SampleProj_Description = "_".join(items)

    elif "somatic" in sUDFs["Analysis"]:
        assay = "wgs-somatic"
        
        #Get paired/unpaired information
        if "paired" in sUDFs["Analysis"] and "unpaired" not in sUDFs["Analysis"]:
            analysis = "paired"
            try:
                pairedSample = sUDFs["Paired Sample Name"]
            except:
                print "Paired Sample Name must be indicated for paired tumor samples"
                sys.exit(255)
        else :
            analysis = "unpaired"
            pairedSample = "X"
            
        #Get Tumor/Normal
        try :
            sampleType = sUDFs["Sample Type"][:1]
        except:
            print "The Sample Type field of the Tumor samples must contain either 'Normalprov' or 'Tumorprov'"
            sys.exit(255)
            
        #Get groupID
        if sampleType == "T" :
            groupID = Name
        elif sampleType == "N" :
            groupID = pairedSample
                        
        try :
            sex = changeDict[ sUDFs["Sex"] ]
        except:
            print "Sex must be indicated for WGS single samples"
            sys.exit(255)
            
        #Set genelist field
        geneList = "other"
        
        #Get department for Coyote
        department = sUDFs["Department"].replace(" ", "")
                            
        if "Topup read count" in sUDFs :
            assay = assay + "-topup"

        items = (assay, 
                 Name, 
                 analysis, 
                 pairedSample, 
                 groupID, 
                 sampleType, 
                 sex, 
                 geneList, 
                 department, 
                 urgent)
        SampleProj_Description = "_".join(items)
                                
    return SampleID,  SampleProj_Description
