class Skip(BaseException):
    """
    Overview:
        Skip signal exception.

        If :class:`Skip` is raised in black-box function of hyper value optimization, \
        it means the current sample will be skipped.
    """
    pass
