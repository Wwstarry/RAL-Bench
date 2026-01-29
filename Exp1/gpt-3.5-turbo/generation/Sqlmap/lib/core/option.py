from lib.core.data import cmdLineOptions, conf


def init():
    """
    Initialize default options and configuration.
    """
    # Defaults
    conf.clear()
    conf.update({
        "url": None,
        "param": None,
        "level": 1,
        "risk": 1,
    })

    cmdLineOptions.clear()
    cmdLineOptions.update({
        "url": None,
        "param": None,
        "level": 1,
        "risk": 1,
    })


def initOptions(options):
    """
    Initialize options from parsed command line arguments.
    """
    if not options:
        return

    # Map options to cmdLineOptions and conf
    if hasattr(options, "url") and options.url is not None:
        cmdLineOptions["url"] = options.url
        conf["url"] = options.url

    if hasattr(options, "param") and options.param is not None:
        cmdLineOptions["param"] = options.param
        conf["param"] = options.param

    if hasattr(options, "level") and options.level is not None:
        cmdLineOptions["level"] = options.level
        conf["level"] = options.level

    if hasattr(options, "risk") and options.risk is not None:
        cmdLineOptions["risk"] = options.risk
        conf["risk"] = options.risk