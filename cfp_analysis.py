import os
import re
import random

def recursive(call, st):
    for i in range(len(st)):
        if call == st[i]:
            return True
    return False

def get_comp(meth, clas, cmp_ar):
    result = [0, 0, 0]
    for i in range(len(cmp_ar)):
        if meth == cmp_ar[i][0] and clas == cmp_ar[i][1]:        
            for j in range(3, 6):
                if cmp_ar[i][j] == "H": 
                    result[j-3] = 1
                else:
                    result[j-3] = 0
            return result
 
    #puts meth + " of " + clas + " not found"
    return result

def get_loc(m_name, c_name, met_ar):
    for i in range(len(met_ar)):
        if m_name == met_ar[i][0] and c_name == met_ar[i][1]:
            return int(met_ar[i][5])
      
    return 0
    
def get_code(m_name, c_name, m_ar):
    code = ""
    for i in range(len(m_ar)):
        if m_name == m_ar[i][0] and c_name == m_ar[i][1]:
            source = open(m_ar[i][3], encoding="utf8")
            code = source.read()
            source.close
            break

    if (code == ""):
        print("code for " + m_name + " in " + c_name + " not found.")
        code = ""
    return code


def remove_comments(code):
    code = re.sub("\"([^\"]|\\.)*\"", "", code)     #remove string literal to avoid /* or // in  a string
    code = re.sub(r"//.*", "", code)  #remove sigle-line comments
    code = re.sub("\'.\'", "\'\'", code)
    com_start = re.compile("/\*")
    com_end = re.compile("\*/")

    s_match = com_start.search(code)
    while  s_match:
        start = s_match.start(0)
        e_match = com_end.search(code)
        end = e_match.end(0)
        code = code[0:start] + code[end:]   #erase the comment
        s_match = com_start.search(code)
    return code

def scan_pac(code):
    i = 0
    ar = list()
    package_decl = re.compile("^[ \t]*package\s+([a-zA-Z\.0-9_$]+)")
    import_decl = re.compile("\s+import\s+((static\s+)?([a-zA-Z\.0-9_$]+))")

    match = package_decl.search(code)
    if match:
        ar.append(match.group(1))
    else:
        ar.append("None")

    for match in import_decl.finditer(code):
        pos = match.end(0)
        ar.append(match.group(1))

    return ar

def get_class_def(cls, code):
    my_regex = "(public|private|protected|static|final|native|synchronized|abstract|threadsafe|transient)*\s+class\s+" + re.escape(cls) + "\s*(extends\s+[a-zA-Z0-9_$]+)?(implements\s+(([a-zA-Z0-9_$]+|\s|,)+))?"

    match = re.search(my_regex, code)   #search for the class definition
    if match:    
        return match.end(0)
    else:
        return 0
    
def get_method_def(met, code):
    modifier = r'(public|private|protected|static|final|native|synchronized|abstract|threadsafe|transient|interface)*'
    generic_type = r'(?:<[a-zA-Z0-9_$\? ,]+>\s+)?'
    method_def = re.compile(modifier + "\s*" + generic_type + "([a-zA-Z0-9_$]+(?:<[a-zA-Z0-9_$\? ,]+>)?)?\s*(\[\])*\s+" + re.escape(met) + "\s*\(\s*")
    match = method_def.search(code)   #search for the method definition
    while match:
        if match.group(2) != "return":
            return match.end(0)
        else:
            match = method_def.search(code, match.end(0))

def parent(cls1, cls2, cls_ar, level):
    if level > len(cls_ar):
        return -1
    else:
        for i in range(len(cls_ar)):
            if cls1 == cls_ar[i][0] and cls2 == cls_ar[i][1]:
                return level
            else:
                l = parent(cls_ar[i][1], cls2, cls_ar, level+1)
                if l > 0:
                    return l
                else:
                    return -1

def get_class(code, m_name, obj, cls, m_def, c_def, met_ar, cls_ar, pacs):
    local = False
    result = list()
    
    if obj is None:        # a local method or a constructor or statically imported
        c_name = cls
        local = True
    else:
        decl = re.compile("([a-zA-Z0-9_$]+)\s+([a-zA-Z0-9_$\[\]]+,[ ]*)*" + re.escape(obj) + "[^a-zA-Z\.0-9_$]")
        match_method = decl.search(code, m_def)
        match_class = decl.search(code, c_def)
        if match_method:
            c_name = match_method.group(1)   
        elif match_class:      #class or interface name
            c_name = match_class.group(1)
        else:           
            c_name = obj      # a class method

    found = False
    for i in range(len(met_ar)):
        if m_name == met_ar[i][0]:   # in scope check? and (local or pacs.include?  met_ar[i][2])
            found = True
            if  c_name == met_ar[i][1]:
                result.append(c_name)
            elif local and m_name == met_ar[i][1]:      #constructor
                result.append(m_name)
            elif "@"+c_name == met_ar[i][1]:     #an interface method
                for i in range(len(cls_ar)):
                    if "@"+c_name == cls_ar[i][1]:
                        impl_cls = cls_ar[i][0]
                        for i in range(len(met_ar)):
                            if m_name == met_ar[i][0] and impl_cls == met_ar[i][1]:     #find the classes that implements the method
                                result.append(impl_cls)
            else:
                for i in range(len(pacs)):
                    if "static" in pacs[i]:
                        names = pacs[i].split(".")
                        if m_name == names[-1]:
                            result.append(names[-2])

    if len(result) == 0 and found:              #inheritance 
        level = 100                               #search for inheritance
        parent_cls = None
        for i in range(len(met_ar)):
            if m_name == met_ar[i][0]:
                n = parent(c_name, met_ar[i][1], cls_ar, 1)     #determine inheritance exists
                if n > 0 and level >= n:
                    parent_cls = met_ar[i][1]
                    level = n
        if parent_cls is None:
            print("Method with no class: " + m_name + " of " + c_name)
        else:
            result.append(parent_cls)
    return result

def count_fp_aux(met, classes, met_ar, cls_ar, cmp_ar, stack, cfps):
    count = 0
    all_fp = [0,0,0,0,0]
    
    for i in range(len(classes)):
        points = count_fp(met, classes[i], met_ar, cls_ar, cmp_ar, stack, cfps)
        if i != len(classes) - 1:                #remove to avoid skipping the computation of ,ethods with the same name
            cfps.pop()
        for j in range(5):
            all_fp[j] += points[j]
        count += 1

    for i in range(5):
        all_fp[i] /= count
    if count > 1:
        print("Average of " + met + " in " + str(classes)+ " is " + str(all_fp) + "\n")
    return all_fp

def get_return_class(m_name, last_mth, met_ar, cls_ar, pacs):
    result = list()

    for i in range(len(met_ar)):
        if last_mth == met_ar[i][0]:        #  and met_ar[i][2] in pacs
            if met_ar[i][1][0] == "@" or re.search("boolean|byte|char|short|int|float|long|double|void|String",met_ar[i][4]):
                next
            else:
                c_name = met_ar[i][4]
                for i in range(len(met_ar)):
                    if m_name == met_ar[i][0] and c_name == met_ar[i][1]:
                        result.append(c_name)
        elif last_mth == met_ar[i][1]:            #calling constructor
            result.append(last_mth)
            break
    return result
        
def count_fp(met, cls, met_ar, cls_ar, cmp_ar, stack, cfps):
    print("\t"*len(stack) + "analyzing "+met+" of "+cls)
    if recursive(cls+"."+met, stack):       #a direct recursice call
        return [0, 0, 0, 0, 0]
    elif (met, cls) in cfps:                #analyzed before
        return [0, 0, 0, 0, 0]
    
    comps = get_comp(met, cls, cmp_ar) 
    loc = get_loc(met, cls, met_ar)
    points = [1, comps[0], comps[1], comps[2], loc]

    code = remove_comments(get_code(met, cls, met_ar))
    p_ar = scan_pac(code)
    class_def = get_class_def(cls, code)     #class variable definition
    met_def = get_method_def(met, code)      #method variable definition

    level = 0                           #the  level outside of the method body
    stack.append(cls+"."+met)
    pattern = re.compile("\{|\}|(([a-zA-Z0-9_$]+)(\[[0-9]+\])?\.)?([a-zA-Z0-9_$]+)\(([^;\{]+)")
    message = re.compile("(([a-zA-Z0-9_$]+)(\[[0-9]+\])?\.)?([a-zA-Z0-9_$]+)\(")
    successive_call = re.compile("\)\.([a-zA-Z0-9_$]+)\(")

    match = pattern.search(code, met_def)
    while match:
        pos = match.end(0)
                
        if match.group(0) == "{":
            level += 1                        #enter a level
        elif match.group(0) == "}":
            level -= 1                        #leave a level
            if level == 0:
                break
        elif match.group(4) is not None:                    
            last_met = match.group(4)                  

            if last_met not in ("if", "for", "while") and met != last_met:   #avoid if(, for(, etc and recurive
                classes = get_class(code, last_met, match.group(2), cls, met_def, class_def, met_ar, cls_ar, p_ar)
                if classes != []:                   #not a call to built in method
                    new_points = count_fp_aux(last_met, classes, met_ar, cls_ar, cmp_ar, stack, cfps)
                    for i in range(5):
                        points[i] += new_points[i]

            rest = match.group(5)
            match = message.search(rest)
            while match:                        #messages calls in parameters
                #print("Inside call for " + rest)
                rest_pos = match.end(0)
                classes = get_class(code, match.group(4), match.group(2), cls, met_def, class_def, met_ar, cls_ar, p_ar)
                if classes != []:
                    new_points = count_fp_aux(match.group(4), classes, met_ar, cls_ar, cmp_ar, stack, cfps)
                    for i in range(5):
                        points[i] += new_points[i]
                match = message.search(rest, rest_pos)

            match = successive_call.search(rest)
            while match:                         #successive messages calls
                #print("Successive call for " + rest)
                rest_pos = match.end(0)
                classes = get_return_class(match.group(1), last_met, met_ar, cls_ar, p_ar)
                if classes != []:
                    new_points = count_fp_aux(match.group(1), classes, met_ar, cls_ar, cmp_ar, stack, cfps)
                    for i in range(5):
                        points[i] += new_points[i]
                match = successive_call.search(rest, rest_pos)

        match = pattern.search(code, pos)
        
    stack.pop()
    cfps.append((met, cls))
    print("\t"*len(stack) + "FP of "+met+" in "+cls +" is "+ str(points))
    return points



met_ar = list()
for met in open("methods.txt", 'r'):
    met = met.rstrip()                        #eliminate new line character
    met_ar.append(met.split(" "))

cls_ar = list()
for cls in open("structure.txt", 'r'):
    cls = cls.rstrip()
    cls_ar.append(cls.split(" "))

cmp_ar = list()
for met in open("comps.txt", 'r'):
    met = met.rstrip()                       #eliminate new line character
    cmp_ar.append(met.split(" "))
  
met = input("method: ")
cls = input("class: ")
cfp = count_fp(met, cls, met_ar, cls_ar, cmp_ar, list(), list())
print("FP of "+ met +" in "+ cls +" is "+ str(cfp))

#choices = random.sample(range(len(cmp_ar)), 25)

##results = open("results.txt", 'w')
##for i in range(len(choices)):
##    cfp = count_fp(cmp_ar[choices[i]][0], cmp_ar[choices[i]][1], met_ar, cls_ar, cmp_ar, list(), list())
##    print("FP of "+cmp_ar[choices[i]][0]+" in "+cmp_ar[choices[i]][1] +" is "+ str(cfp))
##    if cfp[4]>1:
##        results.write(cmp_ar[choices[i]][0] + "," + cmp_ar[choices[i]][1])
##        for i in range(len(cfp)):
##            results.write("," + str(cfp[i]))
##        results.write("\n")
##results.close()
