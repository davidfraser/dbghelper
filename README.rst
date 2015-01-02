dbghelper
=========

Little script that allows you to:

.. code-block:: python

    import dbg ; dbg.D()

as an alternative to:

.. code-block:: python

    import pdb ; pdb.set_trace()

This will launch winpdb if present (i.e. the GUI session gets set up automatically), and fall back to pdb if not. 
