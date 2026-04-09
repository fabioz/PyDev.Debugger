from _pydevd_bundle.pydevd_extension_api import StrPresentationProvider
from .pydevd_helpers import find_mod_attr


class PyTorchTensorFormStr:
    def can_provide(self, type_object, type_name):
        torch_tensor_class = find_mod_attr('torch', 'Tensor')
        return torch_tensor_class is not None and issubclass(type_object, torch_tensor_class)

    def get_str(self, val):
        return "torch.Tensor [ %s , %s ]: %r" % (val.shape, val.device, val)


import sys

if not sys.platform.startswith("java"):
    StrPresentationProvider.register(PyTorchTensorFormStr)
