# Copyright (C) 2013-2014 by Zhang Li <zhangli10 at baidu.com>
# All rights reserved.
#
# vim-javacomplete_ex:
#   improved vim-javacomplete, add following features:
#       1. complete a class name.
#       2. add 'import' statement for a given class.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the project nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE PROJECT AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE PROJECT OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

import vim
import os
import re
import string
import subprocess
import threading
import zlib
import base64
import zipfile

def __GetBootstrapClassPath():
    ## mkdir
    temp_dir = "/tmp/JavaAutoImport.%s.%s" % (os.getlogin(), os.getpid())
    os.mkdir(temp_dir)

    ## write class file
    temp_classfile = temp_dir + "/_.class"

    with open(temp_classfile, "w") as classfile:
        classfile_data = zlib.decompress(base64.b64decode(
            ## simple java class displaying Property "sun.boot.class.path":
            """
            eJxtUMtOwkAUPVeghVoFQfCJysZUFyVxi3Fj4oooCYaNCzLFCZb0QdqpCZ+lCzUu
            /AA/yngHTYiRWdzXnHPm3Pn8ev8AcIaWBROVEjZQLaJmcd60UEfDxJaJbYJx7ke+
            uiDknJMBIX8Z30tCuetH8joLPZncCi/gST4UfkRoOHfdiXgU7UBE43ZfJX407mii
            1Y+zZCSvfA02hq4G2SiiZGLHxi72CLU0i1wvjpU7CkSaulOhHmzso2niwMYhjgg0
            JFQW+jfeRI7Un1F/lioZst0444v6jxk/bvfYiWI/UoQdwupYql4ST2WiZoRjZ4nn
            /yN2uESNYE51F/D29WVCA7Rg8CfrswLSO3O0uGtyJs6F01fQExdsjKMxH+YYZmPt
            F+rMqYD9jJVq7g35FxQWDItvWYZrzV2fP1T+BtBRZv0= """))
        classfile.write(classfile_data)

    ## read classpath from pipe
    classpath = string.join((os.getenv("CLASSPATH"), temp_dir), ":")
    pipe = subprocess.Popen((__java(), "-cp", classpath, "_"), stdout=subprocess.PIPE)
    bootstrap_classpath = pipe.stdout.read().strip()

    ## clean
    os.remove(temp_classfile)
    os.rmdir(temp_dir)
    return bootstrap_classpath


## configuration values
__java = lambda: vim.eval("g:JavaCompleteEx_JavaHome") + "/bin/java"

__bootstrapClassPath = __GetBootstrapClassPath()
__classname_mapping = {}

__classpath = lambda: __bootstrapClassPath + ":" + vim.eval("g:JavaCompleteEx_ClassPath")
__classpath_current = ""


def __AddRelativeFilename_into_ClassNameMapping(relative_filename, classname_mapping):
    if re.match(r"(\w+/)*\w+\.class", relative_filename):
        classname_with_scope_splits = relative_filename.replace(".class", "").split("/")
        classname, scope = (
                classname_with_scope_splits[-1],
                string.join(classname_with_scope_splits[ :-1], "."))

        if not classname_mapping.has_key(classname):
            classname_mapping[classname] = []
        classname_mapping[classname].append(scope)


def __GetClassNameMappingFromDir(dirpath):
    classname_mapping = {}
    try:
        ## walk dirpath
        for root, dirs, filenames in os.walk(dirpath):
            for filename in filenames:
                relative_filename = os.path.relpath(root + "/" + filename, dirpath)
                __AddRelativeFilename_into_ClassNameMapping(relative_filename, classname_mapping)

        return classname_mapping

    except Exception:
        return {}


def __GetClassNameMappingFromJar(jar_filename):
    classname_mapping = {}
    try:
        for relative_filename in zipfile.ZipFile(jar_filename, "r").namelist():
            __AddRelativeFilename_into_ClassNameMapping(relative_filename, classname_mapping)
        return classname_mapping

    except Exception:
        return {}


def __GetClassNameWithScope(classname_mapping, classname):
    if classname_mapping.has_key(classname):
        return list((scope +"." + classname) for scope in classname_mapping[classname])
    return []


def __UpdateClassNameMapping():
    global __classpath_current
    if __classpath_current == __classpath():  ## classpath not changed -- no need to update
        return

    __classname_mapping.clear()

    ## process classpath:
    for classpath in map(string.strip, __classpath().split(":")):

        ## try add jar
        if classpath.endswith(".jar"):
            for classname, scopes in __GetClassNameMappingFromJar(classpath).items():
                if not __classname_mapping.has_key(classname):
                    __classname_mapping[classname] = []
                __classname_mapping[classname].extend(scopes)

        ## try add dir
        else:
            for classname, scopes in __GetClassNameMappingFromDir(classpath).items():
                if not __classname_mapping.has_key(classname):
                    __classname_mapping[classname] = []
                __classname_mapping[classname].extend(scopes)

    ## update classpath_current
    __classpath_current = __classpath()


## utility vim functions
def __vim_cur_classname_with_scope(*args):
    curline = "<%s>" % __vim_curline()
    word_l = __vim_getx() + 1
    word_r = __vim_getx()

    while curline[word_l - 1].isalnum() or curline[word_l - 1] == '_' or curline[word_l - 1] == '.':
        word_l -= 1
    while curline[word_r + 1].isalnum() or curline[word_r + 1] == '_' or curline[word_r + 1] == '.':
        word_r += 1
    return curline[word_l : word_r + 1]

__vim_numlines = lambda *args: int(vim.eval("line('$')"))
__vim_gety     = lambda *args: int(vim.eval("line('.')")) - 1
__vim_getx     = lambda *args: int(vim.eval(" col('.')")) - 1

__vim_addline  = lambda *args: vim.eval("append('%d','%s')" % (args[0] + 1, args[1]))
__vim_getline  = lambda *args: vim.eval("getline('%d')" % (args[0] + 1))
__vim_curline  = lambda *args: vim.eval("getline('.')")
__vim_curword  = lambda *args: vim.eval("expand('<cword>')")


def __vim_InsertImport(classname_with_scope):
    new_import = "import %s;" % classname_with_scope
    line_items = []

    ## extract all non-empty lines
    for nline in range(0, __vim_numlines()):
        if __vim_getline(nline) != "":
            line_items.append( (nline, __vim_getline(nline)))

    line_items.append( (__vim_numlines(), ""))

    ## old imports existed -- add new import alphabetically
    last_import_item = None

    for line_item in line_items:
        if re.match(r"import [\w.]+;", line_item[1]):
            last_import_item = line_item

            if line_item[1] >= new_import:
                if line_item[1] != new_import:
                    __vim_addline(line_item[0] - 1, new_import);
                    return True
                else:
                    return False

    if last_import_item != None:  ## add to last import line
        __vim_addline(last_import_item[0], new_import);
        return True

    ## old imports not existed -- add new import in front of code, excluding 'package bla.bla'
    if re.match(r"package [\w.]+;", line_items[0][1]):
        __vim_addline(0, new_import);  ## first line is 'package bla', add to next line
    else:
        __vim_addline(-1, new_import);  ## add to first line
    return True


def __vim_interface_JavaCompleteEx_AddImport():
    __UpdateClassNameMapping()
    index_userinput = 0
    classname_with_scope = __GetClassNameWithScope(__classname_mapping, __vim_curword())

    ## no candidate
    if classname_with_scope.__len__() == 0:
        print "JavaCompleteEx: classname '%s' not found in any scope." % __vim_curword()
        return

    else:
        ## multiple candidate -- select one from user input
        if classname_with_scope.__len__() > 1:
            for index_classname in enumerate(classname_with_scope):
                print "candidate [%d]: %s" % index_classname

            try:  ## will ignore invalid user input
                index_userinput = int(vim.eval("input('select one candidate: ', '0')"))
                vim.command(":redraw!")
            except:
                print "JavaCompleteEx: invalid input."
                return

        ## insert selected classname
        if __vim_InsertImport(classname_with_scope[index_userinput]):
            print "JavaCompleteEx: class '%s' import done." % classname_with_scope[index_userinput]
            return
        else:
            print "JavaCompleteEx: class '%s' already imported." % classname_with_scope[index_userinput]
            return


def __vim_interface_JavaCompleteEx_CompleteClassName(findstart, base):
    classname_with_scope = __vim_cur_classname_with_scope()

    if int(findstart) == 1:
        curline = __vim_curline()
        start = __vim_getx()

        if classname_with_scope == "" or re.match(r"^[A-Z][A-Za-z0-9_]*$", classname_with_scope):
            while start > 0 and (curline[start - 1].isalnum() or curline[start - 1] == "_"):
                start -= 1
        return start

    else:

        complete_items = []

        if classname_with_scope == "" or re.match(r"^[A-Z][A-Za-z0-9_]*$", classname_with_scope):
            for classname, scopes in __classname_mapping.items():
                if classname.startswith(base):
                    for scope in scopes:
                        complete_items.append({
                                    "word": classname,
                                    "menu": scope,
                                    "kind": "c"})

        complete_items.sort(key=lambda item: item["word"])
        return complete_items.__repr__()


## update mapping immediately after loading plugin
##      updating is done with another thread, so that users will not fall into block
if __name__ == "__main__":
    update_thread = threading.Thread(target=__UpdateClassNameMapping)
    update_thread.start()
    __classpath_current = __classpath()
