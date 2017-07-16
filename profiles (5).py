import os
import re
import fnmatch

def remove_comments(code):
    code = re.sub(r"//.*", "", code)  #remove sigle-line comments
    code = re.sub("\'.\'", "\'\'", code)
    com_start = re.compile("/\*")
    com_end = re.compile("\*/")

    s_match = com_start.search(code)
    while  s_match:
        start = s_match.start(0)         
        e_match = com_end.search(code)
        if e_match:
            end = e_match.end()
            code = code[0:start] + code[end:] #erase the comment
        else:
            print("comment_error")
        s_match = com_start.search(code)
    code = re.sub("\"([^\"]|\\.)*\"", "", code)     #remove string literal to avoid /* or // in  a string
    #code = re.sub(r"//.*", "", code)  #remove sigle-line comments
    #code = re.sub("\'.\'", "\'\'", code)    
    return code

def extract_cyclomatic(code, pos):
    cyclo = 1
    level = 0                                   #prcessing the main body
    symbol = re.compile("\{|\}|\?|[^a-zA-Z0-9_$](if|for|while)(\s+)?\([^;\{]+")
    logical = re.compile("\?\?|\|\|")

    match = symbol.search(code, pos)
    while match:
        pos = match.end()
        
        if match.group(0) == "{" and code[pos] != "'":             # avoid the case of '{' and chinese character
            level += 1  #enter a level
        elif match.group(0) == "}" and code[pos] != "'":
            level -= 1                                    #leave a level
            if level == 0:
                return cyclo
        elif match.group(0) == "?":
            cyclo += 1
        else:
            cyclo += 1
          
            for logical_op in logical.finditer(match.group(0)):
                cyclo += 1
                
        match = symbol.search(code, pos)
        
def extract_body(code, pos, coupling, basic_types, responses):
    level = 0                                   #processing the main body
    loc = 0
    symbol = re.compile("\{|\}|\n|[^a-zA-Z0-9_$](new)\s+([a-zA-Z0-9_$<>]+)|([a-zA-Z0-9_$]+(\[[0-9]+\])?\.)?([a-zA-Z0-9_$]+)\(")

    #print(code[pos:pos+25])
    match = symbol.search(code, pos)
    while match:
        pos = match.end()
        
        if match.group(0) == "\n":              #newline
            loc += 1
        elif match.group(0) == "{" and code[pos] != "'":             # avoid the case of '{' and chinese character
            level += 1  #enter a level
            #print("{" + str(level))
        elif match.group(0) == "}" and code[pos] != "'":
            #print(str(level) + "}")
            level -= 1                                    #leave a level
            if level == 0:
                return loc, pos, responses, coupling 
        elif match.group(1) == "new":
            c_name = match.group(2)
            if c_name not in basic_types:
                if c_name not in responses:
                    responses.append(c_name)
                match = re.match(r"ArrayList<([a-zA-Z0-9_$<>]+)>", c_name)
                if match:
                    if match.group(1) not in basic_types and match.group(1) not in coupling:
                        coupling.append(match.group(1))
                else:
                    if c_name not in coupling:
                        coupling.append(c_name)
        else:
            called = match.group(3)
            if called not in ("if", "for", "while") and called not in responses:    # a method call
                responses.append(called)
                
        match = symbol.search(code, pos)
    return loc, pos, responses, coupling

def get_class(arg_type, basic_types):
    if arg_type in basic_types:
        return None
    else:
        match = re.match(r"ArrayList<([a-zA-Z0-9_$<>]+)>", arg_type)
        if match:
            if match.group(1) in basic_types:
                return None
            else:
                return match.group(1)
        else:
            return arg_type

def extract_method_profile(code, pos, c_name, pname, fname):
    modifier = r'(public|private|protected|static|final|native|synchronized|abstract|class|interface)*'
    generic_type = r'(?:<[a-zA-Z0-9_$\? ,]+>\s+)?'
    return_type = r'([a-zA-Z0-9_$]+(?:<[a-zA-Z0-9_$<>\? ,]+>)?)?\s*(\[\])*'
    m_decl = re.compile(modifier + "\s*" + generic_type + return_type + "\s+" + name + "\s*\(\s*")
    parameter = re.compile("(final\s+)?([a-zA-Z0-9_$]+(?:<[a-zA-Z0-9_$<>\? ,]+>)?)\s*(\[\]|\.\.\.)*\s+([a-zA-Z0-9_$]+)(\[\])*\s*")

    inner_cs = class_decl.search(code, pos)       
    m_header = m_decl.search(code, pos)
    right_bra = r_bra.search(code, pos)
    #print(m_header.group(0))

    while m_header:
        if "." in c_name and right_bra.end() < m_header.end():      # out of an inner class
            class_name = c_name[:c_name.rfind(".")]
            print(class_name)
            pos = extract_method_profile(code, right_bra.end(), class_name, package, fullname)
        elif inner_cs and inner_cs.end() < m_header.end():     #there is a inner class
            if inner_cs.group(2) == "class":
                class_name = c_name + "." + inner_cs.group(3)
                if inner_cs.group(4) is not None:                          #there is a superclass
                    structure.write(class_name + " " + inner_cs.group(5) + "\n")
                    if inner_cs.group(6) is not None:                          #implenments an interface
                        interfaces = inner_cs.group(7).split(",")
                        for i in range(len(interfaces)):
                            structure.write(class_name + " " + "@" + interfaces[i].lstrip() + "\n")
            else:
                class_name = c_name + "." + "@" + inner_cs.group(3)                   #interface declaration
            print(class_name)

            pos = extract_method_profile(code, l_bra.search(code, inner_cs.end()).end(), class_name, package, fullname)
        else:
            pos = m_header.end()

            if m_header.group(2) != "new" and m_header.group(2) != "else" and m_header.group(2) != "return":    
                meth = m_header.group(4)
                if (m_header.group(2)):
                    ret_type = (m_header.group(2)).replace(' ','')
                else:
                    ret_type = ""
                args = ""
                coupling = list()

                print("\t"+meth)
                if code[pos] != ")":                        #not empty parameter
                    para = parameter.search(code, pos)
                    
                    while para:
                        pos = para.end()
                        arg = (para.group(2)).replace(' ','')
                        #print(arg)
                        args += " " + arg
                        a_class = get_class(arg, basic_types)            # if the argument is a class
                        if a_class is not None and a_class not in coupling:
                            coupling.append(arg)                
                        if code[pos] == ")":
                            break                           #end of parameters
                        para = parameter.search(code, pos)

                        
                loc = 0
                if "@" not in c_name and ((m_header.group(1) and "abstract" not in m_header.group(1))
                                          and (m_header.group(2) and "abstract" not in m_header.group(2))):
                    #cyclo = extract_cyclomatic(code, pos)
                    cyclo = 0
                    
                    #print("/nCOU:"+str(code))
                    loc, pos, responses, coupling = extract_body(code, pos, coupling, basic_types, list())
                    #print("LOC:"+str(loc)+"/nPOS"+str(pos)+"/nRES:"+str(responses)+"/nCOU:"+str(coupling))
                    metrics.write(meth + " " + c_name  + " " + pname + " " + str(cyclo) + " " + str(len(responses)) + " " + str(len(coupling)) +"\n")
                profile.write(meth + " " + c_name  + " " + pname + " " + fname + " " + ret_type + " " + str(loc) + args +"\n")
            
        inner_cs = class_decl.search(code, pos)    
        m_header = m_decl.search(code, pos)
        right_bra = r_bra.search(code, pos)
    return pos

def pareto(ar): 
    threshold = 0
    done = False
    while not done:
        count = 0
        for i in range(len(ar)):
            if (int(ar[i]) <= threshold):
                count += 1
        threshold += 1
        if count >= len(ar)*0.8:   #reach the threshhold
            done = True
    return threshold
    
profile = open("methods.txt", "w")
structure = open("structure.txt", 'w')
metrics = open("metrics.txt", 'w')
package_decl=re.compile("package\s+([a-zA-Z\.0-9_$]+)")
modifier = r'(public|private|protected|static|final|native|synchronized|abstract|threadsafe|transient)*'
name = r'([a-zA-Z0-9_$]+)'
inherit = r'(extends\s+([a-zA-Z0-9_$]+))?'
implement = r'(implements\s+(([a-zA-Z0-9_$]+(?:<[a-zA-Z0-9_$\? ,]+>)?|\s|,|\n)+))?'
class_decl = re.compile(modifier + "\s+(class|interface)\s+" + name + "(?:<[a-zA-Z0-9_$\? ,]+>)?" + "\s*" + inherit + "\s*" + implement)
basic_types = ("boolean", "byte", "Byte", "char", "short", "Short", "int", "Integer", "float", "Float", "long", "long", "double", "Double", "String", "Character", "Object")
l_bra = re.compile("{")
r_bra = re.compile("}")

for root, dirs, files in os.walk('.'):
    for fname in files:
        fullname = os.path.join(root, fname)
        if fnmatch.fnmatch(fname, '*.java'):
            print(fullname)
            source = open(fullname, encoding="ISO-8859-1")
            code = source.read()
            source.close()
            code = remove_comments(code)

            match = package_decl.search(code)
            package = match.group(1) if match else "This"

            match = class_decl.search(code, 0)
            while match:                     # in case there is more than one class (if is, may be buggy
                if match.group(2) == "class":
                    class_name = match.group(3)
                    if match.group(4) is not None:                          #there is a superclass
                        structure.write(class_name + " " + match.group(5) + "\n")
                    if match.group(6) is not None:                          #implenments an interface
                        interfaces = match.group(7).split(",")
                  
                        for i in range(len(interfaces)):
                            structure.write(class_name + " " + "@" + interfaces[i].lstrip() + "\n")
                else:
                    class_name = "@" + match.group(3)                   #interface declaration
                print(class_name)
                
                pos = extract_method_profile(code, l_bra.search(code, match.end()).end(), class_name, package, fullname)
                match = class_decl.search(code, pos)

structure.close()
profile.close()
metrics.close()

comp_ar = list()
for met in open("metrics.txt", 'r'):
    met = met.rstrip()                       #eliminate new line character
    comp_ar.append(met.split(" "))
metrics.close()

cyclomat_ar = list()
response_ar = list()
coupling_ar = list()
for i in range(len(comp_ar)):
    cyclomat_ar.append(comp_ar[i][3])
    response_ar.append(comp_ar[i][4])
    coupling_ar.append(comp_ar[i][5])

cyclo_thresh = 11
resp_thresh = pareto(response_ar)
coup_thresh = pareto(coupling_ar)

#print("Threshhold is "+str(threshhold))
comps = open("comps.txt", 'w')

for i in range(len(comp_ar)):
    for j in range(3):
        comps.write(comp_ar[i][j] + " ")
    if (int(comp_ar[i][3]) < cyclo_thresh):
        comps.write("L" +" ")
    else:
        comps.write("H" +" ")
    if (int(comp_ar[i][4]) < resp_thresh):
        comps.write("L" +" ")
    else:
        comps.write("H" +" ")
    if (int(comp_ar[i][5]) < coup_thresh):
        comps.write("L" +"\n")
    else:
        comps.write("H" +"\n")
        
comps.close()



