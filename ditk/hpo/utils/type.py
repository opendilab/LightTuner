from functools import partial
from types import FunctionType, BuiltinFunctionType, MethodType, BuiltinMethodType, LambdaType

try:
    from types import MethodWrapperType, MethodDescriptorType, ClassMethodDescriptorType, WrapperDescriptorType
except ImportError:
    WrapperDescriptorType = type(object.__init__)
    MethodWrapperType = type(object().__str__)
    MethodDescriptorType = type(str.join)
    ClassMethodDescriptorType = type(dict.__dict__['fromkeys'])

_FUNC_TYPES = (
    FunctionType,
    BuiltinFunctionType,
    LambdaType,
    MethodType,
    BuiltinMethodType,
    MethodWrapperType,
    MethodDescriptorType,
    ClassMethodDescriptorType,
    WrapperDescriptorType,
    partial,
)


def is_function(f):
    return isinstance(f, _FUNC_TYPES)
