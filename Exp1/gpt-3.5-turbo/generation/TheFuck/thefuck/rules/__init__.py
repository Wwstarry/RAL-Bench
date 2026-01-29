from . import git
from . import general
from . import apt
from . import docker

rules = []
rules.extend(git.rules)
rules.extend(general.rules)
rules.extend(apt.rules)
rules.extend(docker.rules)