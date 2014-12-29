dbghelper
=========

Little script that allows you to:

    import dbg ; dbg.D()

as an alternative to

    import pdb ; pdb.set_trace()

This will launch winpdb if present (i.e. the GUI session gets set up automatically), and fall back to pdb if not
