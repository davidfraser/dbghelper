dbghelper
=========

Convenience method for manually inserting tracepoints into code that support multiple debuggers

.. code-block:: python

    import dbg ; dbg.D()

as an alternative to:

.. code-block:: python

    import pdb ; pdb.set_trace()

This supports multiple debuggers; currently `pdb <https://docs.python.org/2/library/pdb.html>`_
(or `Pdb++ <https://pypi.python.org/pypi/pdbpp/>`_ if installed), `winpdb <http://winpdb.org>`_, and
`pydevd <http://pydev.org/manual_adv_debugger.html>`_ (which is used inside both
`PyDev <http://pydev.org/>`_ and `PyCharm <https://www.jetbrains.com/pycharm/>`_).

Selecting the debugger
----------------------

The debugger desired can be selected by setting the environment variable PYDBG. The following are valid values:

* ``pydevd`` or ``pycharm`` will use pydevd locally (if running in debug mode) or remotely if not
* ``pydevd_remote`` or ``pycharm_remote`` will use pydevd remotely
* ``pydevd_local`` or ``pycharm_local`` will use pydevd locally, and warn if not running in debug mode
* ``winpdb`` will use winpdb
* ``pdb`` will use pdb  (default)

An environment variable is used so that imports of the debugger libraries can be determined at import time.

Inserting a tracepoint
----------------------

Call ``dbg.D()`` to insert a tracepoint in the code; the appropriate debugger should launch when that line of code
is executed, ready to execute the following line.

A thread-safe version ``dbg.tsD()``is also supported. This is only different when using ``pdb``; in that case multiple
threads having tracepoints (for example, in a web server) can cause confusion as multiple debug sessions get attached
to the same console. The ``tsD`` implementation uses a lock to only allow one debug session to use the console at once;
other sessions are not allowed the lock until the debug interaction is finished (e.g. typing ``c`` for continue).

Parameters for debuggers
------------------------
Some debuggers have parameters that can be set using environment variables, or at runtime.

``pydevd`` implementation will use the value of the environment variables ``PYDEVD_HOST`` for hostname and
``PYDEVD_PORT`` for port when connecting remotely by default. These can also be adjusted on by setting
``dbg.pydevd_args.host`` and ``dbg.pydevd_args.port`` at runtime.

