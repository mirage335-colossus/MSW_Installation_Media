#!/usr/bin/env python3
"""Small local QEMU monitor helper used only for installer verification."""
import argparse
import json
import socket
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('socket')
p.add_argument('command', choices=['hmp', 'execute', 'type', 'screenshot', 'quit', 'query-status'])
p.add_argument('argument', nargs='?')
a = p.parse_args()
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(a.socket)
f = s.makefile('rwb', buffering=0)
def receive():
    while True:
        result = json.loads(f.readline())
        if 'event' not in result:
            return result
def execute(command, arguments=None):
    f.write((json.dumps({'execute': command, 'arguments': arguments or {}})+'\n').encode())
    result = receive()
    if 'error' in result:
        raise RuntimeError(result)
    return result.get('return')
receive()
execute('qmp_capabilities')
if a.command == 'hmp':
    print(execute('human-monitor-command', {'command-line': a.argument}))
elif a.command == 'execute':
    req=json.loads(a.argument)
    print(execute(req['command'],req.get('arguments')))
elif a.command == 'type':
    punctuation = {' ': 'spc', '.': 'dot', ',': 'comma', '/': 'slash',
                   '\\': 'backslash', ':': 'shift-semicolon', ';': 'semicolon',
                   '-': 'minus', '_': 'shift-minus', '=': 'equal', '+': 'shift-equal',
                   '"': 'shift-apostrophe', "'": 'apostrophe', '(': 'shift-9',
                   ')': 'shift-0', '$': 'shift-4', '>': 'shift-dot', '<': 'shift-comma',
                   '*': 'shift-8', '?': 'shift-slash', '!': 'shift-1', '~': 'shift-grave_accent',
                   '|': 'shift-backslash', '\n': 'ret'}
    for char in a.argument:
        if char in punctuation:
            key = punctuation[char]
        elif char.isascii() and char.isalnum():
            key = ('shift-' if char.isupper() else '') + char.lower()
        else:
            raise ValueError('Unsupported test input character: '+repr(char))
        execute('human-monitor-command', {'command-line': 'sendkey '+key+' 20'})
        time.sleep(0.04)
elif a.command == 'screenshot':
    out = Path(a.argument).resolve()
    ppm = out.with_suffix('.ppm')
    execute('screendump', {'filename': str(ppm)})
    from PIL import Image
    Image.open(ppm).save(out)
    ppm.unlink()
    print(out)
else:
    print(execute(a.command))
