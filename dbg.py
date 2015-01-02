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
import warnings

# conditionally imported modules
rpdb2, rpdb2_error = None, None
pydevd, pydevd_error = None, None
pdb, pdb_error = None, None

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

def declare_ts_pdb():
    class TSPdb(pdb.Pdb):
        """A Thread-locked version of the pdb debugger (so it can only run in one thread at a time)"""
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

def ts_pdb_set_trace():
    """A thread-safe version of pdb.set_trace(); if called from multiple threads only one will debug at a time, until continue or quit"""
    TSPdb().set_trace(sys._getframe().f_back)

def pydevd_set_trace():
    """A version of pydevd.settrace that reads the host and port from pydevd_args to activate pycharm's remote debugger"""
    args = pydevd_args
    pydevd._set_trace_lock.acquire()
    try:
        pydevd._locked_settrace(host=args.host, stdoutToServer=True, stderrToServer=True, port=args.port,
                                suspend=False, trace_only_current_thread=False,
                                overwrite_prev_trace=False, patch_multiprocessing=False)
    finally:
        pydevd._set_trace_lock.release()

def pycharm_set_trace():
    """Tell pycharm debugger to pause here"""
    debugger = pydevd.GetGlobalDebugger()
    if debugger is None:
        warnings.warn("Tracepoint from dbg.D ignored as pycharm not running in debug mode", stacklevel=2)
        return
    debugger.SetTraceForFrameAndParents(pydevd.GetFrame(), False)
    # Trace future threads
    debugger.patch_threads()
    thread = threading.current_thread()
    if not hasattr(thread, "additionalInfo"):
        thread.additionalInfo = pydevd.PyDBAdditionalThreadInfo()
    pydevd.pydevd_tracing.SetTrace(debugger.trace_dispatch)
    debugger.setSuspend(thread, pydevd.CMD_THREAD_SUSPEND)

_user_pref = os.getenv('PYDBG', 'winpdb').lower()
class pydevd_args:
    host = os.getenv("PYDEVD_HOST", "") or None
    port = int(os.getenv("PYDEVD_PORT", "") or "5678")
_active_debugger = None

if _user_pref == 'remote_pycharm':
    try:
        import pydevd
        _active_debugger = 'remote_pycharm'
    except ImportError, pydevd_error:
        pass
elif _user_pref == 'pycharm':
    try:
        import pydevd
        _active_debugger = 'pycharm'
    except ImportError, pydevd_error:
        pass
elif _user_pref == 'winpdb':
    try:
        import rpdb2
        _active_debugger = 'winpdb'
    except ImportError, rpdb2_error:
        pass
else: # if _user_pref == 'pdb':
    try:
        import pdb
        _active_debugger = 'pdb'
    except ImportError, pdb_error:
        pass

if _active_debugger == 'remote_pycharm':
    tsD = D = pydevd_set_trace
elif _active_debugger == 'pycharm':
    if not pydevd.connected:
        warnings.warn("dbg.D has pycharm configured as debugger, but process not running in debug mode")
    tsD = D = pycharm_set_trace
elif _active_debugger == 'winpdb':
    tsD = D = rpdb2_with_winpdb
elif _active_debugger == 'pdb':
    TSPdb = declare_ts_pdb()
    D = pdb.set_trace
    tsD = ts_pdb_set_trace
else:
    D = lambda: warnings.warn("Attempt to set debugger tracepoint, but no debugger available", stacklevel=2)
    tsD = D

