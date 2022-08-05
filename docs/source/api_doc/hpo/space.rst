lighttuner.hpo.space
==========================

.. currentmodule:: lighttuner.hpo.space

.. automodule:: lighttuner.hpo.space


BaseSpace
------------------

.. autoclass:: BaseSpace
    :members: length, count


ContinuousSpace
------------------

.. autoclass:: ContinuousSpace
    :members: __init__, lbound, ubound, length, count


SeparateSpace
------------------

.. autoclass:: SeparateSpace
    :members: __init__, start, end, step, length, count


FixedSpace
------------------

.. autoclass:: FixedSpace
    :members: __init__, length, count

