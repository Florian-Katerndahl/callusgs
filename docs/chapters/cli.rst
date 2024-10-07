.. _cli_tools:

CLI Tools
=========

``callusgs`` provides four command-line interface tools detailed below.

.. note::
    When supplying coordinates on the command line as is shown below, you need to end the coordinate string with two dashes (`--`).
    This stops the program from trying to parse any further arguments. In turn, this also means the AOI must be given as the last argument!

.. autoprogram:: callusgs.cli:parent_parser
    :prog: callusgs
