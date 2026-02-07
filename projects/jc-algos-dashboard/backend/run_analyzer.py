#!/usr/bin/env python3
"""
Wrapper script to run analyzer scripts with correct Python path.
This handles the path differences between host and container environments.
"""
import sys
import os

# Determine base path (different in Docker container vs host)
if os.path.exists('/clawd'):
    BASE = '/clawd'
else:
    BASE = '/root/clawd'

# Add required paths
sys.path.insert(0, os.path.join(BASE, 'projects', 'market-analyzer'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))

# Patch the original script's path expectations
import builtins
_original_open = builtins.open
def patched_open(file, *args, **kwargs):
    if isinstance(file, str):
        # Replace /root/clawd with container path if needed
        if file.startswith('/root/clawd') and BASE != '/root/clawd':
            file = file.replace('/root/clawd', BASE)
    return _original_open(file, *args, **kwargs)
builtins.open = patched_open

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: run_analyzer.py <script> [args...]")
        sys.exit(1)
    
    script = sys.argv[1]
    # Adjust script path for container
    if script.startswith('/root/clawd') and BASE != '/root/clawd':
        script = script.replace('/root/clawd', BASE)
    
    # Read and exec the script
    sys.argv = sys.argv[1:]  # Remove this script from argv
    
    # Execute the target script
    with open(script, 'r') as f:
        code = f.read()
        # Fix hardcoded paths in the code
        code = code.replace('/root/clawd', BASE)
        exec(compile(code, script, 'exec'), {'__name__': '__main__', '__file__': script})
