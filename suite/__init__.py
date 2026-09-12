"""The task suite: the world the loop is judged on.

A tool-using coding agent runs over a fixed suite of small tasks, each graded
by hidden tests, through a tool layer with injected transient faults: an HTTP
tool that returns a transient 5xx on a fixed fraction of first calls, a shell
tool with a call budget, and a file tool. The faults exist so that lessons
are learnable across passes and the oracle can score whether they were
learned.
"""

EVALUATION = "suite-v1"
