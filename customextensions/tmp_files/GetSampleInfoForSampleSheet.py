import re
import sys

def getMICROinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument):
    SampleID = sLimsID + "_" + planID
    #Index Example: A701-A503 (ATCACGAC-TGTTCTCT)
    I7_ID = Index.split('-')[0]
    I5_ID = re.search(r'\-(.*)\s', Index).group(1)

    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)
    if "NextSeq" in instrument or "MiniSeq" in instrument:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Get Species
    if "S. aureus" in sUDFs["Reference Genome"] :
        species = "s.aureus"
    else:
        print "Reference Genome must be chosen for microbiology samples"
        sys.exit(255)

    #Sample Project and Description Field
    tokens = Name.split("_")
    
    SampleProj_Description = ",microbiology_" + tokens[0] + "_" + species

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description

def getRNASEQinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument):
    SampleID = sLimsID + "_" + planID

    #Index Example: A03 UD00001 (ATCACGAC-TGTTCTCT)
    I7_ID = Index.split(' ')[1]
    I5_ID = Index.split(' ')[1]
    
    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)

    if "NextSeq" in instrument or "MiniSeq" in instrument:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))
                    
    #Analysis
    #fusioncatcher
    if "TruSeq Stranded mRNA - Fusion" in sUDFs["Analysis"] :
        Analysis = "rnaseq-fusion"
        if "Diagnosis" in sUDFs:
            SampleProj_Description = ",rnaseq-fusion_" + Name + "_" + sUDFs["Diagnosis"]
        else:
            SampleProj_Description = ",rnaseq-fusion_" + Name + "_rnaseq-fusion"

    #bladderclassifier
    elif "TruSeq Stranded mRNA - Bladder" in sUDFs["Analysis"] :
        SampleProj_Description = ",rnaseq-bladder_" + Name + "_rnaseq-bladder"

    #alignment and STAR
    else:
        SampleProj_Description = ",rnaseq_" + Name + "_rnaseq"

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description


def getNIPTinfo(planID, DOM, Name, Index, sLimsID, instrument):
    SampleID = sLimsID + "_" + planID

    #Index example: A1 p704-p504 (CACCGGGA-CGATATGA)
    p7p5 = Index.split(' ')[1]
    I7_ID = p7p5[0:2] + "-" + p7p5[2:4]
    I7_ID = p7p5[5:7] + "-" + p7p5[7:9]
    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)
    if "NextSeq" in instrument or "MiniSeq" in instrument:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Sample Project and Description Field
    SampleProj_Description = "NIPT,nipt_" + Name

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description

def getMYELOIDinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument):

    DiagnosisDict = { "Hematologisk neoplasi" : "AML" ,
                      "KLL" : "KLL",
                      "MPN" : "MPN" , 
                      "Annat" : "Annat", 
                      "Hematologisk neoplasi efter transplantation" : "AlloSCT" }

    #Index Example: A701-A503 (ATCACGAC-TGTTCTCT)
    I7_ID = Index.split('-')[0]
    I5_ID = re.search(r'\-(.*)\s', Index).group(1)

    I7_Index = re.search(r'\((.*)\-', Index).group(1)
    I5_Index = re.search(r'[A|T|G|C]{8}\-(.*)\)', Index).group(1)
    if "NextSeq" in instrument or "MiniSeq" in instrument:
        #Get reverse complement of Index 5
        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Get Tumor/Normal
    if "normal" in sUDFs["Sample Type"] :
        SampleType = "N"
    elif "malignitet" in sUDFs["Sample Type"] :
        SampleType = "T"
    else:
        print "The Sample Type field of the Myeloid samples must contain either Vavnadsbiopsi normal or Hematologisk malignitet"
        sys.exit(255)

    #Get Diagnosis
    if (('Hematologisk neoplasi' in sUDFs["Diagnosis"]) or ('KLL' in sUDFs["Diagnosis"]) or ('Annat' in sUDFs["Diagnosis"]) or ('MPN' in sUDFs["Diagnosis"]) or ('Hematologisk neoplasi efter transplantation' in sUDFs["Diagnosis"])):
        Diagnosis = sUDFs["Diagnosis"]
    else :
        print "Sample Diagnosis must be either Hematologisk neoplasi, KLL, MPN, Annat or Hematologisk neoplasi efter transplantation for the Myeloid samples"
        sys.exit(255)

    #Get paired/unpaired information
    if "Myeloisk Panel - Parad" in sUDFs["Analysis"] :
        Analysis = "paired"
        PairedSample = sUDFs["Paired Sample Name"]
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
            SampleProj_Description = ",myeloid_N" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + DiagnosisDict[Diagnosis]
        else:
            SampleProj_Description = ",myeloid_N" + tokens[0] + "_" + Analysis + "_N" + PairedSample + "_" + SampleType + "_X"

    elif tokens[1] == 'LNP' :
        SampleID = sLimsID + "_" + planID
        if PairedSample == "X":
            #Unpaired 
            SampleProj_Description = ",myeloid_" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + DiagnosisDict[Diagnosis]
        else: 
            SampleProj_Description = ",myeloid_" + tokens[0] + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_X"
    else :
        print "The workflow identifiers 'CAN2' or 'LNP' must be appended to the Library name"
        sys.exit(255)

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description
                
def getEXOMEinfo(planID, DOM, Name, Index, sLimsID, sUDFs, instrument):
    SampleID = sLimsID + "_" + planID
    #Index Example: A01 (GTCTGTCA)
    I7_ID = Index.split(' ')[0]
    I5_ID = "MolBC"
    
    I7_Index = re.search(r'\s\((.*)\)$', Index).group(1)
    I5_Index = "NNNNNNNNNN"
#    if "NextSeq" in instrument or "MiniSeq" in instrument:
#        #Get reverse complement of Index 5
#        complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}
#        I5_Index = "".join(complement.get(base, base) for base in reversed(I5_Index))

    #Sample Project and Description Field
    #Trio example: exome _3901-15_3901-15_proband_M_affected_neuro
    #Single example: exome _3213-16_X_X_M_affected_ahus
    #Tumour example: exome-tumor_8776-17_paired_8775-17_T_F_neuroblastom
    # BRCA example: exome-brca_1111-12_BRCA

    if "Diagnosis" in sUDFs:
        if sUDFs["Diagnosis"] == "Pediatrik":
                                Application = "pediatrics"
        elif sUDFs["Diagnosis"] == "Annat":
                                Application = "other"
        elif ( (sUDFs["Diagnosis"] == "aHUS") or (sUDFs["Diagnosis"] == "complement") ):
                                Application = sUDFs["Diagnosis"]
        else :
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
                          "CMT/Neuropati" : "cmt-neuropati", 
                          "Ataxi" : "ataxi", 
                          }
                          
            #Kanalopati,Bindv:avssjukdomar,Komplex kardiologi,Kardiomyopati,RASopati,PAH HHT CM-AVM, Anpassad
            #Kanalopati,Bindvavssjukdomar,Komplex-kardiologi,Kardiomyopati,RASopati,PAH-HHT-CM-AVM, Anpassad   

            #More than one gene list
            if "," in sUDFs["Gene list"] :
                tmp = []
                Genelist = sUDFs["Gene list"].split(", ")
                for Glist in Genelist :
                    if (re.match(r'^Bindv.*vssjukdomar$', Glist )) :
                        tmp.append("Bindvavssjukdomar")

                    elif (re.match(r'^H.*rselneds.*ttning$', Glist )) :
                        tmp.append("Horselnedsattning")
                    
                    elif (re.match(r'^Heredit.*r Spastisk Parapares$', Glist )) :
                        tmp.append("hsp")

                    else:
                        try : 
                            tmp.append( geneLists[ Glist ] )
                        except:
                            print "The gene list field must contain one of the following option: Kanalopati,Bindv:avssjukdomar,Komplex kardiologi,Kardiomyopati,RASopati, H:orselneds:attning, Anpassad, PAH HHT CM-AVM, CMT/Neuropati, Heredit:ar Spastisk Parapares or Ataxi. If more than one gene lists are used, please use ',' as seperator."
                            sys.exit(255)

                tmp = ("+").join(tmp)
                Application =  tmp

            #Only one gene list
            else :
                if (re.match(r'^Bindv.*vssjukdomar$', sUDFs["Gene list"] )) :
                    Application = "Bindvavssjukdomar"

                elif (re.match(r'^H.*rselneds.*ttning$', sUDFs["Gene list"] )) :
                    Application = "Horselnedsattning"

                elif (re.match(r'^Heredit.*r Spastisk Parapares$', sUDFs["Gene list"] )) :
                    Application = "hsp"

                else :
                    try:
                        Genelist = geneLists[ sUDFs["Gene list"] ]
                        Application = Genelist
                    except:
                        print "The gene list field must contain one of the following option: Kanalopati,Bindv:avssjukdomar,Komplex kardiologi,Kardiomyopati,RASopati, H:orselneds:attning, Anpassad, PAH HHT CM-AVM, CMT/Neuropati, Heredit:ar Spastisk Parapares or Ataxi."
                        sys.exit(255)

        else:
            print "The diagnosis field must contain either aHUS, complement, Annat or Pediatrik"
            sys.exit(255)


    if ( (sUDFs["Analysis"] == "SureSelectXTHS - Trio Exome") or (sUDFs["Analysis"] == "SureSelectXTHS - Single Exome") or (sUDFs["Analysis"] == "SureSelectXTHS - Paired Tumor Exome")or (sUDFs["Analysis"] == "SureSelectXTHS - Unpaired Tumor Exome") ):

        #For these samples, gender must be indicated
        if "Sex" in sUDFs:
            if sUDFs["Sex"] == "Man":
                sex = "M"
            elif sUDFs["Sex"] == "Kvinna":
                sex = "F"
            elif (re.match(r'^Ok.*nt$', sUDFs["Sex"] )) :
                sex = "U"
            else :
                print "Man, Kvinna or Okant must be indicated for the SureSelect XTHS samples"
                sys.exit(255)
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
                print "The Sample Type field must contain either Sjuk or Frisk"
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
        
            SampleProj_Description = ",exome_" + Name + "_" + sUDFs["FamilyID"] + "_" + pedigree + "_" + sex + "_" + Type + "_" + Application

        #Single samples
        elif sUDFs["Analysis"] == "SureSelectXTHS - Single Exome" :
            SampleProj_Description = ",exome_" + Name + "_" + "X" + "_" + "X" + "_" + sex + "_affected_" + Application

        #Tumor Samples
        elif "Tumor" in sUDFs["Analysis"]:
            #Get paired/unpaired information
            if "Paired Tumor Exome" in sUDFs["Analysis"] :
                Analysis = "paired"
                PairedSample = sUDFs["Paired Sample Name"]
            elif "Unpaired Tumor Exome" in sUDFs["Analysis"] :
                Analysis = "unpaired"
                PairedSample = "X"
            else :
                print "Tumor analysis must be either 'SureSelectXTHS - Paired Tumor Exome' or 'SureSelectXTHS - Unpaired Tumor Exome'"
                sys.exit(255)

            #Get Tumor/Normal
            if "Normal" in sUDFs["Sample Type"] :
                SampleType = "N"
            elif "Tum" in sUDFs["Sample Type"][:3] :
                SampleType = "T"
            else:
                print "The Sample Type field of the SureSelect Tumor samples must contain either 'Normalprov' or 'Tumorprov'"
                sys.exit(255)

            #Get department for Coyote
            department = sUDFs["Department"].replace(" ", "") 

            SampleProj_Description = ",exome-tumor_" + Name + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + sex + "_" + Application + "_" + department

    elif ("BRCA" in sUDFs["Analysis"] ) :
        #BRCA samples

        #Get paired/unpaired information
        if "Paired BRCA" in sUDFs["Analysis"] :
            Analysis = "paired"
            PairedSample = sUDFs["Paired Sample Name"]

            #Get Tumor/Normal
            if "Normal" in sUDFs["Sample Type"] :
                SampleType = "N"
            elif "Tum" in sUDFs["Sample Type"][:3] :
                SampleType = "T"
            else:
                print "The Sample Type field of the SureSelect Paired BRCA samples must contain either 'Normalprov' or 'Tumorprov'"
                sys.exit(255)

        elif "Unpaired BRCA" in sUDFs["Analysis"] :
            Analysis = "unpaired"
            PairedSample = "X"
            SampleType = "X" 
        else :
            print "BRCA analysis must be either 'SureSelectXTHS - Paired BRCA' or 'SureSelectXTHS - Unpaired BRCA'"
            sys.exit(255)

        SampleProj_Description = ",brca_" + Name + "_" + Analysis + "_" + PairedSample + "_" + SampleType + "_" + Application

    elif ("CTG" in sUDFs["Analysis"] ) :
        #CTG exome samples
        SampleProj_Description = ",exome-ctg_" + Name #+ "_" + Application

    else:
        print "Trio, Single, Tumor, CTG or BRCA must be indicated in the analysis field for the SureSelect XTHS samples"
        sys.exit(255)

    return SampleID, I7_ID, I7_Index, I5_ID, I5_Index, SampleProj_Description
