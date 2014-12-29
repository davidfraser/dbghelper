#!/usr/bin/env python

"""inline-debugging helper script. allows calling either pdb or winpdb in a similar fashion, from a single line of code:
    import dbg ; dbg.D()
"""

import os
import random
import string
import sys
import time
import threading

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
    if WIN_PDB_SESSION is None:
        print >>sys.stderr, "Launching WinPDB and connecting to this session"
        pid = os.fork()
        if pid:
            WIN_PDB_SESSION = pid
            rpdb2.start_embedded_debugger(password, depth=depth + 1)
        else:
            time.sleep(0.2)
            winpdb_script = "; ".join(WINPDB_SCRIPT) % {"password": password, "filename": filename}
            os.execl(sys.executable, "python", "-c", winpdb_script)
    else:
        rpdb2.start_embedded_debugger(password, depth=depth + 1)


_user_pref = os.getenv('PYDBG', 'winpdb').lower()
rpdb2 = None

if _user_pref == 'winpdb':
    try:
        import rpdb2
    except ImportError, e:
        pass

if rpdb2 is None:
    import pdb
    D = pdb.set_trace

    class TSPdb(pdb.Pdb):
        tsl = threading.RLock()
        local = threading.local()
        def set_continue(self):
            pdb.Pdb.set_continue(self)
            if TSPdb.local.level:
                while TSPdb.local.level >= 1:
                    TSPdb.local.level -= 1
                    TSPdb.tsl.release()

        def set_quit(self):
            pdb.Pdb.set_quit(self)
            if TSPdb.local.level:
                while TSPdb.local.level >= 1:
                    TSPdb.local.level -= 1
                    TSPdb.tsl.release()

        def set_trace(self, frame=None):
            TSPdb.tsl.acquire()
            if not hasattr(TSPdb.local, "level"):
                TSPdb.local.level = 0
            TSPdb.local.level += 1
            # repeat the pdb code so we don't get an additional level of dispatching
            if frame is None:
                frame = sys._getframe().f_back
            self.reset()
            while frame:
                frame.f_trace = self.trace_dispatch
                self.botframe = frame
                frame = frame.f_back
            self.set_step()
            sys.settrace(self.trace_dispatch)


    def ts_set_trace():
        TSPdb().set_trace(sys._getframe().f_back)

    tsD = ts_set_trace
else:
    tsD = D = rpdb2_with_winpdb

