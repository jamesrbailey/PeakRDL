Processing Input
================

File order and linking
----------------------

The PeakRDL command line tool is capable of processing multiple input files and
linking them together. Component declarations are added to a common namespace
that is shared across files, allowing components to be instantiated in another file.

Since PeakRDL processes and links files in-order, it is important to provide the
list of files in the correct sequence - dependencies first, top-level last:

.. code-block:: bash

    peakrdl <command> subblock1.rdl subblock2.rdl top.rdl


Top-level elaboration
---------------------
Unless specified otherwise, PeakRDL will elaborate the last addrmap component
that was declared in the root namespace.

For example, given the following input file:

.. code-block:: systemrdl
    :name: example.rdl

    addrmap common {
        reg {
            field {} spam_y;
        } spam_x;
    };

    addrmap foo {
        common block_a;
        common block_b;
    };

    addrmap bar {
        common block_x;
        common block_y;
    };

By default, PeakRDL will elaborate ``bar`` as the top-level node, since it is last:

.. code-block:: bash

    $ peakrdl dump example.rdl
    0x0-0x3: bar.block_x.spam_x
    0x4-0x7: bar.block_y.spam_x

Or you can explicitly choose an alternative addrmap to elaborate using the ``--top`` flag:

.. code-block:: bash

    $ peakrdl dump example.rdl --top foo
    0x0-0x3: foo.block_a.spam_x
    0x4-0x7: foo.block_b.spam_x

If you are not sure what targets are available as top-levels, you can list all
that are available using the ``globals`` command:

.. code-block:: bash

    $ peakrdl globals example.rdl
    common
    foo
    bar


Exporting a sub-hierarchy
-------------------------
``--top`` chooses a component from the root namespace. To export something
further down the hierarchy instead, add ``--instance`` with a hierarchical
instance path, relative to that top:

.. code-block:: bash

    $ peakrdl dump example.rdl --top bar --instance block_x
    0x0-0x3: bar.block_x.spam_x

The two work together: ``--top`` picks the component to elaborate, and
``--instance`` picks the subtree of it to export. ``--instance`` on its own
resolves against whichever addrmap would be elaborated by default, which is
the last one declared, so it is usually worth naming the top explicitly.

Unlike ``--top``, this selects an *instance* rather than a type, so the
parameter values that the surrounding design applies to it are honoured and do
not have to be restated with ``-P``. One case is the same addrmap instantiated
more than once with different parameters:

.. code-block:: systemrdl
    :name: params.rdl

    addrmap foo #(longint unsigned WIDTH = 1) {
        reg {
            field {} baz[WIDTH];
        } bar;
    };

    addrmap top {
        foo #(.WIDTH(2)) u_a;
        foo #(.WIDTH(7)) u_b;
    };

Each instance can be exported with the width written on it in the RDL, without
restating it with ``-P``:

.. code-block:: bash

    $ peakrdl dump params.rdl --top top --instance u_a -F
    0x0-0x3: top.u_a.bar
        [1:0] baz

    $ peakrdl dump params.rdl --top top --instance u_b -F
    0x4-0x7: top.u_b.bar
        [6:0] baz

The same applies to a parameter that is set high in the hierarchy and
propagated down, where ``--top`` would lose the value even though the
sub-block is only instantiated once:

.. code-block:: systemrdl
    :name: propagated.rdl

    addrmap foo #(longint unsigned WIDTH = 1) {
        reg {
            field {} baz[WIDTH];
        } bar;
    };

    addrmap qux #(longint unsigned WIDTH = 1) {
        foo #(.WIDTH(WIDTH)) u_foo;
    };

    addrmap top {
        qux #(.WIDTH(9)) u_qux;
    };

``--instance`` elaborates ``foo`` in its real context, so ``WIDTH`` arrives
through ``qux`` as the design intends. ``--top`` elaborates the type on its
own, falling back to the default:

.. code-block:: bash

    $ peakrdl dump propagated.rdl --top top --instance u_qux.u_foo -F
    0x0-0x3: top.u_qux.u_foo.bar
        [8:0] baz

    $ peakrdl dump propagated.rdl --top foo -F
    0x0-0x3: foo.bar
        [0:0] baz

The second result is silently wrong for the design, and correcting it means
restating every propagated parameter with ``-P`` and keeping those values in
step with the RDL by hand.

Only the exported subtree changes. Whether addresses are those of the full
design or rebased to the sub-hierarchy is up to the exporter.

.. note::

    As with ``--top``, ``--instance`` paths must resolve to an addrmap.
    Pointing it at a regfile, memory, register or field is an error.

Elements of an array instance are selected by index, as ``u_arr[2]``. An
unindexed path exports the array's shared definition, though some exporters
require an explicit index. A path segment of ``^`` refers to the parent
instance, as long as the result stays within the top component.



Supported Input Formats
-----------------------

PeakRDL can support intermixing various input formats.


SystemRDL 2.0
^^^^^^^^^^^^^

SystemRDL is the primary register model source format for PeakRDL.

For a full description of the register description language standard, see
`Accellera's SystemRDL 2.0 specification <http://accellera.org/downloads/standards/systemrdl>`_.

Internally, PeakRDL uses the `systemrdl-compiler <https://systemrdl-compiler.readthedocs.io>`_ package
to interpret and elaborate RDL input.


IP-XACT XML
^^^^^^^^^^^

PeakRDL is capable of importing IP-XACT XML files. These are converted into SystemRDL semantics by the importer.
For more details on how the importer works, see the `PeakRDL-ipxact documentation <https://peakrdl-ipxact.readthedocs.io/en/latest/importer.html>`_.

For more details on the IP-XACT format, see `Accellera's standards page <https://www.accellera.org/downloads/standards/ip-xact>`_



Your custom importer extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PeakRDL's capabilities can be extended with your own custom importer plugin.
See more details here: :ref:`importer-plugin`
