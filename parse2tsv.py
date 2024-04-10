#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 10:28:57 2019
 parse2tsv expects a directory path which must include a single .dat, .yml and file
 These are used  to read the fixed withd .dat file and write
 all the contents into two sets of tab separated files {H,H_aux}.tsv (household records) and {P,P_aux}.tsv 
 (person records).
 
 The procedure must:
     1) find the .dat file and the .yml file
        - process the yml to extract info on structure of file
     2) read a line determine if it is an H or P record
     3) parse the line ie. separate it into varialbes based on information
         - REMOVE all \t TAB characters from each variable string
     4) write the proper parts to each of the files
     

@author: test-ipums
"""
#%%
import yaml
import struct
import os
import sys
import re
#%%
if len(sys.argv) !=2 :
    print("Can't do nothing without a directory")
    print("sys.argv[0] <path to dir>")
    quit()

xdir=sys.argv[1]
if os.path.isdir(xdir) :
    pass
else:
    print("{} sucks at being a directory".format(xdir))
    quit()
#%%
#xdir='../1930_3-3'    
#%%

def getFOrDie(sufx,xdir=xdir):
    """
    returns the one and only file with the give suffix in the directory or dies
    """
    files=os.listdir(xdir)
    #yfiles=[x for x in files if sufx in x]
    #resufx='sufx'+'$'
    yfiles=[x for x in files if re.search(sufx ,  x)]
    if len(yfiles) != 1:
        print("must be exactly one {} file in {}, found {}:{}".format(sufx,xdir,len(yfiles),yfiles))
        quit()
        
    else:
        return("/".join([xdir,yfiles[0]]))
        

#%%
def yaml2struct(ymvars):
    """
    expects a list of dicts harvested from IPUMS us_19xx....yaml  file.  Specifically
    the list stored as 'variables'  BUT filtered to only include either rectype='H' or 'P'
    """
    position=1        
    fwidth=[]
    vname=[]
    for v in ymvars:

        cstart=v['start_column']
        cwidth=v['width']
        
        filler=0
        if cstart < position :
            print("finished parsing after {} vars".format(len(vname)))
            break
        fmt="s"
            # there are no double to test this so let's not bother all shall be string
            #if v['is_double_var'] & v['width'] == 8:
            #    fmt='d'
        if cstart == position:
            
        
            fwidth.append("{}{}".format(cwidth,fmt))
            vname.append(v['name'])
        if cstart > position:
            filler=cstart-position
            fwidth.append("{}{}".format(filler,"x"))
            fwidth.append("{}{}".format(cwidth,fmt))
            vname.append(v['name'])
            position+=filler
        #print('''name:{0} cw={1} pos={2} sc={3} '''.format(v["name"],cwidth,position,cstart))

        position+=cwidth
        
        fmtstring=' '.join(fwidth)
        fieldstruct=struct.Struct(fmtstring)
        parseX=fieldstruct.unpack_from
    print("""digested {} variable specs for:""".format(len(vname)))
    print("""{}""".format(vname))
        
    return({"vname":vname,"fwidth":fwidth,"parse":parseX})
#%% 
#def OBSOLETEprocess_line(line,parseH=Hr['parse'],parseP=Pr['parse']):
#    """
#    handles one line from the data file - determines if H/P parses and writes
#    """
#    if line[0] == 'H':
#        flds=parseH(bytes(line,'utf-8'))
#        H.write("\t".join([str(x) for x in flds])+"\n")
#        
#    if line[0] == 'P':
#        flds=parseP(bytes(line,'utf-8'))
#        P.write("\t".join([str(x) for x in flds])+"\n")
#      
#           
#        
#        if counth % 10000 == 0:
#            print('H',end='')
#        if countp % 10000 == 0:
#            print('P',end='')
#        if (counth + countp) % 100000 ==0 :
#            print('')
#            #H.flush()
#%%
    
def NOTUSEDgetStataVarTypes(statado):
    """
    reads the provided statado file and creates a dict of infix types keyed by varname
    """    
    s=open(statado,'r')
    stdo=list(s)
    s.close()
    statTypes={}
    infix=False
    for sline in stdo :
        if not infix and  re.search('quietly infix',sline):
            infix=True
            continue
        
                
        if infix and re.search('using',sline ) :
            infix=False
            continue
        if infix:    
            #print(sline)    
            vtype,vname,cols,junk =sline.split()
            statTypes[vname]=vtype
    return(statTypes)

#%%    
#xdir="../1930_3-3"

    
Hout=xdir+"/H.tsv"
Pout=xdir+"/P.tsv"    
HoutAux=xdir+"/H_aux.tsv"
PoutAux=xdir+"/P_aux.tsv"    

dfile=getFOrDie(r'.*\.dat$')
yml=getFOrDie(r'.*\.yml$')
statado=getFOrDie(r'.*\.do$')
# deal with the yaml file
with open(yml, 'r') as myfile:
    data=myfile.read()#.replace('\n', '')
    
ymdat=yaml.load(data)    

##stataType=getStataVarTypes(statado)

#fieldwidths=[x['width'] for x in ymdat['variables']]

#%%
# select the list of variabls that are H and P records creat list of yaml elements
# do not include USA19X0D_NNN varialbes -- those will go in auxillary files
Hvars=[x for x  in ymdat['variables'] if x['record_type'] == 'H' and not re.search('US19.*\d{2}',x['name'])]    
Pvars=[x for x  in ymdat['variables'] if x['record_type'] == 'P' and not re.search('US19.*\d{2}',x['name'])]    

# create an object that identifies the columns and allows for easy parsing later
Hr=yaml2struct(Hvars)   
Pr=yaml2struct(Pvars)   


HvarsAux=[x for x  in ymdat['variables'] if x['record_type'] == 'H' and re.search('US19.*\d{2}',x['name'])]    
PvarsAux=[x for x  in ymdat['variables'] if x['record_type'] == 'P' and re.search('US19.*\d{2}',x['name'])]

## sames structures for auxiliary vars but include serial/pernum for matching later
serial_column=[h['name'] for h in Hvars].index('SERIAL')
HvarsAux.insert(0,Hvars[serial_column])
HrAux= yaml2struct(HvarsAux)

serial_column=[p['name'] for p in Pvars].index('SERIALP')
pernum_column=[p['name'] for p in Pvars].index('PERNUM')

idlist=[serial_column,pernum_column]
idlist.sort()
PvarsAux.insert(0,Pvars[idlist[1]])
PvarsAux.insert(0,Pvars[idlist[0]])

PrAux= yaml2struct(PvarsAux)  
#%%
# =============================================================================
# fmtstringH=' '.join(Hr['fwidth'])
# fieldstructH=struct.Struct(fmtstringH)
# parseH=fieldstructH.unpack_from
# 
# fmtstringP=' '.join(Pr['fwidth'])
# fieldstructP=struct.Struct(fmtstringP)
# parseP=fieldstructP.unpack_from
# =============================================================================

      

parseH=Hr['parse']
parseP=Pr['parse']
parseHAux=HrAux['parse']
parsePAux=PrAux['parse']
bufsize=655360
#f=open(dfile,'rb')
P=open(Pout,'w')
H=open(Hout,'w')
Paux=open(PoutAux,'w')
Haux=open(HoutAux,'w')
H.write("\t".join(Hr["vname"])+"\n")
P.write("\t".join(Pr["vname"])+"\n")
Haux.write("\t".join(HrAux["vname"])+"\n")
Paux.write("\t".join(PrAux["vname"])+"\n")
counth=0
countp=0
with open(dfile,'rb') as f:
    while True:
        lines=f.readlines(bufsize)
        if not lines :
            break
        for line in lines :
            #if line[0] == 'H':
            if line[0] == 72:
                #flds=parseH(bytes(line,'ascii'))
                flds=parseH(line)
                fldt=[x.decode('ascii',"replace") for x in flds]   
                fldt=[x.replace("\t","_") for x in fldt]                

                H.write("\t".join(fldt)+"\n")
                ## same for aux file
                flds=parseHAux(line)
                fldt=[x.decode('ascii',"replace") for x in flds]
                fldt=[x.replace("\t","_") for x in fldt]                
                
                Haux.write("\t".join(fldt)+"\n")

                
                counth+=1
            if line[0] == 80:
                flds=parseP(line)
                fldt=[x.decode('ascii',"replace") for x in flds]
                fldt=[x.replace("\t","_") for x in fldt]                

                P.write("\t".join(fldt)+"\n")
                ## same for aux file
                flds=parsePAux(line)
                fldt=[x.decode('ascii',"replace") for x in flds]
                fldt=[x.replace("\t","_") for x in fldt]                

                Paux.write("\t".join(fldt)+"\n")
 
                countp+=1
           
            print("\rH:{:,} / P:{:,}       ".format(counth,countp),end="")
        #if(counth > 1000000):
        #    print("exiting after 1 millin H records")
        #    break

f.close()
H.close()
P.close()




#line=f.readline()

#with open(dfile, 'r') as myfile:
#   line=myfile.read()#.replace('\n', '')
 
#%%
