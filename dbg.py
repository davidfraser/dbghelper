#!/usr/bin/env python

"""inline-debugging helper script. allows calling either pdb or winpdb in a similar fashion, from a single line of code:
    import dbg ; dbg.D()
"""

import copy
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

pydevd_remote_set_trace = None

def pydevd_local_set_trace():
    """Tell pycharm debugger to pause here (when running locally inside pycharm, already connected to pydevd)"""
    pydevd._set_trace_lock.acquire()
    try:
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
    finally:
        pydevd._set_trace_lock.release()


_user_pref = os.getenv('PYDBG', 'pdb').lower()
class _pydevd_args_type(object):
    _host = os.getenv("PYDEVD_HOST", "") or None
    _port = int(os.getenv("PYDEVD_PORT", "") or "5678")
    @property
    def host(self):
        return getattr(self, "_host")
    @host.setter
    def set_host(self, new_host):
        self._host = new_host
        self._update_defaults()

    @property
    def port(self):
        return self._port
    @port.setter
    def set_port(self, new_port):
        self._port = new_port
        self._update_defaults()

    def update_defaults(self):
        if pydevd_remote_set_trace is not None:
            pydevd_remote_set_trace.func_defaults = (self._host, True, True, self._port, True, False, False, False)

pydevd_args = _pydevd_args_type()
del _pydevd_args_type
_active_debugger = None

if _user_pref.replace("_local", "").replace("_remote", "") in ('pycharm', 'pydevd'):
    try:
        import pydevd
        pydevd_remote_set_trace = copy.copy(pydevd.settrace)
        pydevd_args.update_defaults()
        if _user_pref.endswith("_local"):
            _active_debugger = 'pydevd_local'
        elif _user_pref.endswith("_remote"):
            _active_debugger = 'pydevd_remote'
        else:
            # this is unspecified local/remote - detect if already locally imported otherwise assume remote
            if pydevd.connected:
                _active_debugger = 'pydevd_local'
            else:
                _active_debugger = 'pydevd_remote'
    except ImportError, pydevd_error:
        pass
elif _user_pref == 'winpdb':
    try:
        import rpdb2
        _active_debugger = 'winpdb'
    except ImportError, rpdb2_error:
        pass
elif _user_pref == 'pdb':
    try:
        import pdb
        _active_debugger = 'pdb'
    except ImportError, pdb_error:
        pass

if _active_debugger == 'pydevd_remote':
    tsD = D = pydevd_remote_set_trace
elif _active_debugger == 'pydevd_local':
    if not pydevd.connected:
        warnings.warn("dbg.D has pycharm configured as debugger, but process not running in debug mode")
    tsD = D = pydevd_local_set_trace
elif _active_debugger == 'winpdb':
    tsD = D = rpdb2_with_winpdb
elif _active_debugger == 'pdb':
    TSPdb = declare_ts_pdb()
    D = pdb.set_trace
    tsD = ts_pdb_set_trace
else:
    D = lambda: warnings.warn("Attempt to set debugger tracepoint, but no debugger available", stacklevel=2)
    tsD = D

