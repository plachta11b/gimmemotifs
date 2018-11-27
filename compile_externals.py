import sys
import os
from subprocess import Popen,PIPE
from distutils import log

def compile_simple(name, src_dir="src"):
    path = os.path.join(src_dir, "%s" % name)
    
    if not os.path.exists(path):
        return
    
    try:
        Popen("gcc", stdout=PIPE, stderr=PIPE).communicate()
    except Exception:
        return
    
    Popen(["gcc","-o%s" % name, "%s.c" % name, "-lm"], cwd=path, stdout=PIPE).communicate()
    if os.path.exists(os.path.join(path, name)):
        return True

def compile_configmake(name, binary, configure=True, src_dir="src"):
    path = os.path.join(src_dir, "%s" % name)

    if not os.path.exists(path):
        return
    
    if configure:
        Popen(["chmod", "+x", "./configure"], cwd=path, stdout=PIPE, stderr=PIPE).communicate()
        Popen(["./configure"], cwd=path, stdout=PIPE, stderr=PIPE).communicate()
    Popen(["make"], cwd=path, stdout=PIPE, stderr=PIPE).communicate()

    if os.path.exists(os.path.join(path, binary)):
        return True

def print_result(result):
    if not result:
        log.info("... failed")
    else:
        log.info("... ok")
    
def compile_all(prefix=None, src_dir="src"):
    # are we in the conda build environment?
    conda_build = os.environ.get("CONDA_BUILD")
    
    sys.stderr.write("compiling BioProspector")
    sys.stderr.flush()
    result = compile_simple("BioProspector", src_dir=src_dir)
    print_result(result)

    sys.stderr.write("compiling MDmodule")
    sys.stderr.flush()
    result = compile_simple("MDmodule", src_dir=src_dir)
    print_result(result)
    
    # We don't need to compile MEME for conda
    if not conda_build:
        sys.stderr.write("compiling MEME")
        sys.stderr.flush()
        result = compile_configmake("meme_4.6.0", "src/meme.bin", src_dir=src_dir)
        print_result(result)
        # In line with the conda binary which is also called meme
        os.rename("src/meme.bin", "src/meme")
    
    return
