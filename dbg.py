#!/usr/bin/env python

"""inline-debugging helper script. allows calling either pdb or winpdb in a similar fashion, from a single line of code:
    import dbg ; dbg.D()
"""

import os
import random
import string
import sys
import time

try:
    import rpdb2
except ImportError, e:
    rpdb2 = None
if rpdb2:
    pdb = None
else:
    import pdb

WINPDB_SCRIPT = [
    "import os, sys, winpdb",
    "os.name = 'nt'",
    "winpdb.g_ignored_warnings[winpdb.STR_EMBEDDED_WARNING] = True",
    "sys.argv[:] = ['winpdb', '--attach', '-p', '%(password)s', '%(filename)s']",
    "winpdb.main()",
]

WIN_PDB_SESSION = None

def rpdb2_with_winpdb(depth=0):
    """launches an embedded debugging session in the foreground, and a background winpdb process that automatically connects to it
    If winpdb has already been launched, simply set a trace point"""
    global WIN_PDB_SESSION
    password = "".join(random.sample(string.letters, 10))
    f = sys._getframe(depth + 1)
    filename = rpdb2.calc_frame_path(f)
    print >>sys.stderr, "Launching WinPDB and connecting to this session"
    if WIN_PDB_SESSION is None:
        pid = os.fork()
        if pid:
            WIN_PDB_SESSION = pid
            rpdb2.start_embedded_debugger(password, depth=depth + 1)
        else:
            time.sleep(0.2)
            winpdb_script = "; ".join(WINPDB_SCRIPT) % {"password": password, "filename": filename}
            print winpdb_script
            os.execl(sys.executable, "python", "-c", winpdb_script)
    else:
        rpdb2.start_embedded_debugger(password, depth=depth + 1)

if rpdb2:
    D = rpdb2_with_winpdb
else:
    D = pdb.set_trace

