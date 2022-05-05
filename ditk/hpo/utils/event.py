from enum import Enum
from typing import Dict, Any, Callable, Type, Union

_EventType = Union[Type[Enum], list, tuple]


def _auto_members(events: _EventType):
    if isinstance(events, type) and issubclass(events, Enum):
        return list(events.__members__.values())
    elif isinstance(events, (list, tuple)):
        return list(events)
    else:
        raise TypeError(f'Invalid event set - {repr(events)}.')


class EventModel:
    """
    Overview:
        Event processing model.
    """

    def __init__(self, events: _EventType):
        """
        Constructor of :class:`EventModel`.

        :param events: All the events, can be an enum class or a list of strings.
        """
        self.__listeners: Dict[Any, Dict[str, Callable]] = {event: {} for event in _auto_members(events)}

    def _event(self, event) -> Dict[str, Callable]:
        if event not in self.__listeners:
            raise KeyError(f'Event {repr(event)} not found.')
        return self.__listeners[event]

    def bind(self, event, callback: Callable, name: str = None):
        """
        Bind callback function to an event model.

        :param event: Event to be bound to.
        :param callback: Callback function.
        :param name: Name of this callback, default is ``None`` which means the name of given ``callback`` \
            will be used as name.
        """
        self._event(event)[name or callback.__name__] = callback

    def unbind(self, event, name: Union[str, Callable]):
        """
        Unbind callback function from an event model.

        :param event: Event to be unbound from.
        :param name: Name of the callback, if a callable object is given, its name will be used.
        """
        if callable(name):
            name = name.__name__
        del self._event(event)[name]

    def unbind_all(self, event):
        """
        Unbind all the callback functions of the given ``event``.

        :param event: Event to be unbound from.
        """
        self._event(event).clear()

    def trigger(self, event, *args, **kwargs):
        """
        Event is triggered, notify the callbacks.

        :param event: Event that is triggered.
        :param args: Positional arguments for callback functions.
        :param kwargs: Key-value arguments for callback functions.
        """
        for _, callback in self._event(event).items():
            callback(*args, **kwargs)
