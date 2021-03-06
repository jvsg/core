#!/usr/bin/python

import sys
import re
import io

definitionSet = set()
definitionToSourceLocationMap = dict()
callSet = set()

# clang does not always use exactly the same numbers in the type-parameter vars it generates
# so I need to substitute them to ensure we can match correctly.
normalizeTypeParamsRegex = re.compile(r"type-parameter-\d+-\d+")
def normalizeTypeParams( line ):
    return normalizeTypeParamsRegex.sub("type-parameter-?-?", line)

# The parsing here is designed to avoid grabbing stuff which is mixed in from gbuild.
# I have not yet found a way of suppressing the gbuild output.
with io.open("loplugin.unuseddefaultparams.log", "rb", buffering=1024*1024) as txt:
    for line in txt:
        tokens = line.strip().split("\t")
        if tokens[0] == "defn:":
            access = tokens[1]
            returnType = tokens[2]
            nameAndParams = tokens[3]
            sourceLocation = tokens[4]
            funcInfo = (normalizeTypeParams(returnType), normalizeTypeParams(nameAndParams))
            definitionSet.add(funcInfo)
            definitionToSourceLocationMap[funcInfo] = sourceLocation
        elif tokens[0] == "call:":
            returnType = tokens[1]
            nameAndParams = tokens[2]
            callSet.add((normalizeTypeParams(returnType), normalizeTypeParams(nameAndParams)))

# Invert the definitionToSourceLocationMap.
# If we see more than one method at the same sourceLocation, it's being autogenerated as part of a template
# and we should just ignore it.
sourceLocationToDefinitionMap = {}
for k, v in definitionToSourceLocationMap.iteritems():
    sourceLocationToDefinitionMap[v] = sourceLocationToDefinitionMap.get(v, [])
    sourceLocationToDefinitionMap[v].append(k)
for k, definitions in sourceLocationToDefinitionMap.iteritems():
    if len(definitions) > 1:
        for d in definitions:
            definitionSet.remove(d)

    
tmp1set = set()
for d in definitionSet:
    methodSignature = d[0] + " " + d[1]
    if (methodSignature == "class boost::intrusive_ptr<class FontCharMap> FontCharMap::GetDefaultMap(_Bool)"
        # bunch of methods in here all with the same signature
        or "SwAttrSet::" in d[1] or "SwFormat::" in d[1]):
        continue
    if d in callSet:
        continue
    tmp1set.add((methodSignature, definitionToSourceLocationMap[d]))

# sort the results using a "natural order" so sequences like [item1,item2,item10] sort nicely
def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]

# sort results by name and line number
tmp1list = sorted(tmp1set, key=lambda v: natural_sort_key(v[1]))

# print out the results
with open("loplugin.unuseddefaultparams.report", "wt") as f:
    for t in tmp1list:
        f.write(t[1] + "\n")
        f.write("    " + t[0] + "\n")


