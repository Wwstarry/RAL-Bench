class Context:
    def __init__(self):
        pass

class Exit(SystemExit):
    def __init__(self, code=0):
        self.exit_code = code
        super().__init__(code)

class ParamInfo:
    def __init__(self, default, **kwargs):
        self.default = default
        self.kwargs = kwargs

class OptionInfo(ParamInfo):
    def __init__(self, default, param_decls, **kwargs):
        super().__init__(default, **kwargs)
        self.param_decls = param_decls

class ArgumentInfo(ParamInfo):
    pass