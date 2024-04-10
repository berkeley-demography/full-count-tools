#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  5 09:46:56 2017

This will read a .do file (especially one donwloaded from IPUMS) and will
output a set of factor() calls that one might run in R if you happened to 
read the thing in as a csv file.

Apr 17 2018 update: duplicate levels are a thing in ipums do files but are no longer OK
in R.  this deals with the problem by appending 'X's to level elements until all are unique

@author: carlm
"""
#%%
#import csv
import sys
import re
#%%
#dofile='usa_00137.do'

## for debugging
#with open(dofile) as f:
#    content = f.readlines()

#%%
content=[]
for line in sys.stdin:
    
    content.append(line)
#%% 
def apndDupe(labs) :
    """
    expects a list of strings; appends an 'X' to each element that is not unique
    repeats until all elements are unique
    """
    seen=set()
    uniq=[]
    for x in labs:
        while x in seen:
            x=x+'X'
        seen.add(x)
        uniq.append(x)
    return(uniq)        
            
#%%    
# save only label define lines
vars={}
for row in content :
  
    m=re.search('^\s*label\s+define\s+(\S+)\s+(\S+)\s+[ "`]+([\w\s+-\\\]+)',row)

    if m:
        #print(row)
        #print(m.group(1)+'|'+m.group(2) + '|' + m.group(3))
        (vname,level,label)=(m.group(1),m.group(2),m.group(3))
        if not vname in list(vars.keys()):
            vars[vname]=[[],[]]
        
        vars[vname][0].append(level)
        vars[vname][1].append(label)
#%%
for v in vars.keys():
    vname=str.replace(v,"_lbl","").upper()
 
    
    # do files sometimes have duplicates in labels --which is no longer OK in R::factor
    # append X to duplicate labels as we wonder why this should be so
    vars[v][1]=apndDupe(vars[v][1])
    labels=', '.join('"' + item + '"' for item in vars[v][1])
    ## note need for {{  and }} inside tripple quotes
    cmd= """
        {0}<-function(x,strings=FALSE,na2na=TRUE) {{
            res<-factor(as.character(factor(x,levels=c({2}),labels=c({3}))))
            if(na2na){{
                #levels(res)[levels(res)=="N/A"]<-NA
                levels(res)[grep(levels(res),pattern="N/A")]<-NA
            }}
            if(strings){{
                res<-as.character(res)
            }}
            return(res)
    }}""".format(vname+"_F",vname,','.join(vars[v][0]),labels)
    print(cmd)
