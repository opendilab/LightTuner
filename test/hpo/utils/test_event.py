from enum import IntEnum

import pytest

from lighttuner.hpo.utils import EventModel


class MyEvents(IntEnum):
    START = 1
    STEP = 2
    END = 3


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoUtilsEvent:

    def test_str_list(self):
        model = EventModel(['start', 'step', 'end'])

        cnta, cntb = 0, 1

        def _func_a(x):
            nonlocal cnta
            cnta += x

        def _func_b(x):
            nonlocal cntb
            cntb *= x

        model.bind('start', lambda: _func_a(2))
        model.bind('end', lambda: _func_b(7))
        model.bind('step', _func_a)
        model.bind('step', _func_b)

        model.trigger('start')
        model.trigger('step', 3)
        model.trigger('step', 5)
        model.trigger('end')

        assert cnta == 10
        assert cntb == 105

    def test_enum(self):
        model = EventModel(MyEvents)

        cnta, cntb = 0, 1

        def _func_a(x):
            nonlocal cnta
            cnta += x

        def _func_b(x):
            nonlocal cntb
            cntb *= x

        model.bind(MyEvents.START, lambda: _func_a(2))
        model.bind(MyEvents.END, lambda: _func_b(7))
        model.bind(MyEvents.STEP, _func_a)
        model.bind(MyEvents.STEP, _func_b)

        model.trigger(MyEvents.START)
        model.trigger(MyEvents.STEP, 3)
        model.trigger(MyEvents.STEP, 5)
        model.trigger(MyEvents.END)

        assert cnta == 10
        assert cntb == 105

    def test_enum_type(self):
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            EventModel(int)
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            EventModel(233)

    def test_bind(self):
        model = EventModel(MyEvents)

        cnta, cntb = 0, 1

        def _func_a(x):
            nonlocal cnta
            cnta += x

        def _func_b(x):
            nonlocal cntb
            cntb *= x

        with pytest.raises(KeyError):
            model.bind('step', _func_a)
        with pytest.raises(KeyError):
            model.bind(12, _func_a)
        with pytest.raises(KeyError):
            model.unbind('step', _func_a)
        with pytest.raises(KeyError):
            model.unbind(12, 'func_a')

        model.bind(MyEvents.START, _func_a)
        model.bind(MyEvents.START, _func_b)
        model.bind(MyEvents.STEP, _func_a)
        model.bind(MyEvents.STEP, _func_b)
        model.bind(MyEvents.END, _func_a)
        model.bind(MyEvents.END, _func_b)

        model.unbind(MyEvents.START, _func_a)
        model.unbind(MyEvents.STEP, _func_b)
        model.unbind(MyEvents.END, "_func_a")

        model.trigger(MyEvents.START, 2)
        model.trigger(MyEvents.STEP, 3)
        model.trigger(MyEvents.STEP, 5)
        model.trigger(MyEvents.END, 7)

        assert cnta == 8
        assert cntb == 14

        model.unbind_all(MyEvents.START)

        model.trigger(MyEvents.START, 2)
        model.trigger(MyEvents.STEP, 3)
        model.trigger(MyEvents.STEP, 5)
        model.trigger(MyEvents.END, 7)

        assert cnta == 16
        assert cntb == 98

        model.unbind_all(MyEvents.STEP)
        model.unbind_all(MyEvents.END)

        model.trigger(MyEvents.START, 2)
        model.trigger(MyEvents.STEP, 3)
        model.trigger(MyEvents.STEP, 5)
        model.trigger(MyEvents.END, 7)

        assert cnta == 16
        assert cntb == 98
