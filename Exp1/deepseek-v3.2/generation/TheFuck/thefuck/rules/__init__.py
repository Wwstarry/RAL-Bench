import os
import importlib.util

_rules_cache = None

def get_rules():
    global _rules_cache
    if _rules_cache is not None:
        return _rules_cache
    
    rules = []
    rules_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(rules_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            module_path = os.path.join(rules_dir, filename)
            
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for Rule class in the module
            for attr_name in dir(module):
                if attr_name.endswith('Rule'):
                    rule_class = getattr(module, attr_name)
                    if hasattr(rule_class, 'is_match') and hasattr(rule_class, 'get_new_command'):
                        rules.append(rule_class())
    
    _rules_cache = rules
    return rules