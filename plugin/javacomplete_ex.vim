" Copyright (C) 2013-2014 by Zhang Li <zhangli10 at baidu.com>
" All rights reserved.
"
" vim-javacomplete_ex:
"   improved vim-javacomplete, add following features:
"       1. complete a class name.
"       2. add 'import' statement for a given class.
"
" Redistribution and use in source and binary forms, with or without
" modification, are permitted provided that the following conditions
" are met:
" 1. Redistributions of source code must retain the above copyright
"    notice, this list of conditions and the following disclaimer.
" 2. Redistributions in binary form must reproduce the above copyright
"    notice, this list of conditions and the following disclaimer in the
"    documentation and/or other materials provided with the distribution.
" 3. Neither the name of the project nor the names of its contributors
"    may be used to endorse or promote products derived from this software
"    without specific prior written permission.
"
" THIS SOFTWARE IS PROVIDED BY THE PROJECT AND CONTRIBUTORS ``AS IS'' AND
" ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
" IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
" ARE DISCLAIMED.  IN NO EVENT SHALL THE PROJECT OR CONTRIBUTORS BE LIABLE
" FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
" DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
" OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
" HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
" LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
" OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
" SUCH DAMAGE.
"
if !exists("loaded_javacomplete_ex")  " load javacomplete_ex script only once
    let loaded_javacomplete_ex=1
else
    finish
endif

" default JAVA_HOME value, used to locate javac/jar/java executables.
let g:JavaCompleteEx_JavaHome=$JAVA_HOME
let g:JavaCompleteEx_ClassPath=$CLASSPATH

" load corresponding .py script
autocmd FileType java :exec "pyfile ".escape(expand("<sfile>:p:h"), "\\")."/javacomplete_ex_impl.py"

" define commands
autocmd FileType java :command -nargs=0 JavaCompleteExAddImport :python __vim_interface_JavaCompleteEx_AddImport()

" omni complete function for completing class names
function! javacomplete_ex#Complete(findstart, base)
    let classname_with_scope = pyeval("__vim_cur_classname_with_scope()")

    if classname_with_scope == "" || classname_with_scope =~ "^[A-Z][A-Za-z0-9_]*$"
        " complete a classname, use JAImportComplete
        return eval(pyeval("__vim_interface_JavaCompleteEx_CompleteClassName(
                    \ vim.eval('a:findstart'),
                    \ vim.eval('a:base'))"))
    else
        " otherwise, use javacomplete#Complete
        return javacomplete#Complete(a:findstart, a:base)
    endif
endfunction
