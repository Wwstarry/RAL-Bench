import sys

def echo(message, file=None, nl=True, err=False):
    if file is None:
        file = sys.stderr if err else sys.stdout
    
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except:
            pass 
            
    print(message, file=file, end='\n' if nl else '')