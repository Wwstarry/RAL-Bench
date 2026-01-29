from .models import OptionInfo, ArgumentInfo

def Option(default, *param_decls, help=None, show_default=True, is_flag=None, **kwargs):
    return OptionInfo(
        default, 
        param_decls, 
        help=help, 
        show_default=show_default, 
        is_flag=is_flag, 
        **kwargs
    )

def Argument(default, *, help=None, show_default=True, **kwargs):
    return ArgumentInfo(
        default, 
        help=help, 
        show_default=show_default, 
        **kwargs
    )