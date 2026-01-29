from .types import CorrectedCommand
from .rules import get_rules

def get_corrected_commands(command):
    corrected_commands = []
    for rule in get_rules():
        if rule.match(command):
            new_commands = rule.get_new_command(command)
            if not isinstance(new_commands, list):
                new_commands = [new_commands]
            
            for n in new_commands:
                if isinstance(n, CorrectedCommand):
                    corrected_commands.append(n)
                else:
                    priority = getattr(rule, 'priority', 1000)
                    corrected_commands.append(CorrectedCommand(n, priority=priority))
    
    return sorted(corrected_commands, key=lambda cmd: cmd.priority)

def organize_commands(corrected_commands):
    seen = set()
    result = []
    for cmd in corrected_commands:
        if cmd.script not in seen:
            seen.add(cmd.script)
            result.append(cmd)
    return result