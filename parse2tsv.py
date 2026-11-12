#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 10:28:57 2019
 parse2tsv expects a directory path which must include a single .dat, .yml and .do file
 These are used  to read the fixed width .dat file and write
 all the contents into two sets of tab separated files {H,H_aux}.tsv (household records) and {P,P_aux}.tsv
 (person records).

 The procedure must:
     1) find the .dat file and the .yml file
        - process the yml to extract info on structure of file
     2) read a line determine if it is an H or P record
     3) parse the line ie. separate it into variables based on information
         - REMOVE all TAB characters from each variable string
     4) write the proper parts to each of the files

 Updated 2026-11: compatible with Python 3.12+ and PyYAML 6+
   - yaml.load() now given an explicit Loader (required by PyYAML 6)
   - regex patterns use raw strings (fixes SyntaxWarning on Python 3.12+)
   - exits with a nonzero status on errors so batch jobs can detect failures
   - progress printed every 100,000 records instead of every line (much faster)
   - all four output files are closed explicitly
   - Python and PyYAML versions printed at start so job logs record the environment

@author: test-ipums
"""
#%%
import yaml
import struct
import os
import sys
import re

print("Python {} | PyYAML {} ({})".format(
    sys.version.split()[0], yaml.__version__, sys.executable))

#%%
if len(sys.argv) != 2:
    print("Can't do nothing without a directory")
    print("{} <path to dir>".format(sys.argv[0]))
    sys.exit(1)

xdir = sys.argv[1]
if not os.path.isdir(xdir):
    print("{} sucks at being a directory".format(xdir))
    sys.exit(1)

#%%

def getFOrDie(sufx, xdir=xdir):
    """
    returns the one and only file with the given suffix in the directory or dies
    """
    files = os.listdir(xdir)
    yfiles = [x for x in files if re.search(sufx, x)]
    if len(yfiles) != 1:
        print("must be exactly one {} file in {}, found {}:{}".format(sufx, xdir, len(yfiles), yfiles))
        sys.exit(1)
    return "/".join([xdir, yfiles[0]])


#%%
def yaml2struct(ymvars):
    """
    expects a list of dicts harvested from IPUMS us_19xx....yaml  file.  Specifically
    the list stored as 'variables'  BUT filtered to only include either rectype='H' or 'P'
    """
    position = 1
    fwidth = []
    vname = []
    for v in ymvars:
        cstart = v['start_column']
        cwidth = v['width']

        if cstart < position:
            print("finished parsing after {} vars".format(len(vname)))
            break
        fmt = "s"  # all fields read as strings
        if cstart == position:
            fwidth.append("{}{}".format(cwidth, fmt))
            vname.append(v['name'])
        if cstart > position:
            filler = cstart - position
            fwidth.append("{}{}".format(filler, "x"))
            fwidth.append("{}{}".format(cwidth, fmt))
            vname.append(v['name'])
            position += filler

        position += cwidth

    fmtstring = ' '.join(fwidth)
    fieldstruct = struct.Struct(fmtstring)
    parseX = fieldstruct.unpack_from
    print("digested {} variable specs for:".format(len(vname)))
    print("{}".format(vname))

    return {"vname": vname, "fwidth": fwidth, "parse": parseX}

#%%
Hout = xdir + "/H.tsv"
Pout = xdir + "/P.tsv"
HoutAux = xdir + "/H_aux.tsv"
PoutAux = xdir + "/P_aux.tsv"

dfile = getFOrDie(r'.*\.dat$')
yml = getFOrDie(r'.*\.yml$')
statado = getFOrDie(r'.*\.do$')

# deal with the yaml file
with open(yml, 'r') as myfile:
    data = myfile.read()

# Use the fast C loader if PyYAML was built with libyaml, otherwise the pure-Python one
SafeLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
ymdat = yaml.load(data, Loader=SafeLoader)

#%%
# select the list of variables that are H and P records, create list of yaml elements
# do not include USA19X0D_NNN variables -- those will go in auxiliary files
AUX_PATTERN = r'US19.*\d{2}'

Hvars = [x for x in ymdat['variables'] if x['record_type'] == 'H' and not re.search(AUX_PATTERN, x['name'])]
Pvars = [x for x in ymdat['variables'] if x['record_type'] == 'P' and not re.search(AUX_PATTERN, x['name'])]

# create an object that identifies the columns and allows for easy parsing later
Hr = yaml2struct(Hvars)
Pr = yaml2struct(Pvars)

HvarsAux = [x for x in ymdat['variables'] if x['record_type'] == 'H' and re.search(AUX_PATTERN, x['name'])]
PvarsAux = [x for x in ymdat['variables'] if x['record_type'] == 'P' and re.search(AUX_PATTERN, x['name'])]

## same structures for auxiliary vars but include serial/pernum for matching later
serial_column = [h['name'] for h in Hvars].index('SERIAL')
HvarsAux.insert(0, Hvars[serial_column])
HrAux = yaml2struct(HvarsAux)

serial_column = [p['name'] for p in Pvars].index('SERIALP')
pernum_column = [p['name'] for p in Pvars].index('PERNUM')

idlist = [serial_column, pernum_column]
idlist.sort()
PvarsAux.insert(0, Pvars[idlist[1]])
PvarsAux.insert(0, Pvars[idlist[0]])

PrAux = yaml2struct(PvarsAux)

#%%
parseH = Hr['parse']
parseP = Pr['parse']
parseHAux = HrAux['parse']
parsePAux = PrAux['parse']
bufsize = 655360
PROGRESS_EVERY = 100000


def clean(flds):
    return "\t".join(x.decode('ascii', "replace").replace("\t", "_") for x in flds) + "\n"


counth = 0
countp = 0
with open(Pout, 'w') as P, open(Hout, 'w') as H, \
     open(PoutAux, 'w') as Paux, open(HoutAux, 'w') as Haux, \
     open(dfile, 'rb') as f:

    H.write("\t".join(Hr["vname"]) + "\n")
    P.write("\t".join(Pr["vname"]) + "\n")
    Haux.write("\t".join(HrAux["vname"]) + "\n")
    Paux.write("\t".join(PrAux["vname"]) + "\n")

    while True:
        lines = f.readlines(bufsize)
        if not lines:
            break
        for line in lines:
            if line[0] == 72:    # 'H'
                H.write(clean(parseH(line)))
                Haux.write(clean(parseHAux(line)))
                counth += 1
            elif line[0] == 80:  # 'P'
                P.write(clean(parseP(line)))
                Paux.write(clean(parsePAux(line)))
                countp += 1

            if (counth + countp) % PROGRESS_EVERY == 0:
                print("\rH:{:,} / P:{:,}       ".format(counth, countp), end="", flush=True)

print("\rH:{:,} / P:{:,}       ".format(counth, countp))
print("done")
