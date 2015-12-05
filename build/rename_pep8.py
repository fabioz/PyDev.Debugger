import re
import os
import names_to_rename

_CAMEL_RE = re.compile(r'(?<=[a-z])([A-Z])')
_CAMEL_DEF_RE = re.compile(r'(def )((([A-Z0-9]+|[a-z0-9])[a-z][a-z0-9]*[A-Z]|[a-z0-9]*[A-Z][A-Z0-9]*[a-z])[A-Za-z0-9]*)')

def _normalize(name):
    return _CAMEL_RE.sub(lambda x: '_' + x.group(1).lower(), name).lower()

def find_matches_in_contents(contents):
    return [x[1] for x in re.findall(_CAMEL_DEF_RE, contents)]
    
def iter_files_in_dir(dirname):
    for root, _dirs, files in os.walk(dirname):
        for filename in files:
            if filename.endswith('.py') and filename not in ('rename_pep8.py', 'names_to_rename.py'):
                path = os.path.join(root, filename)
                with open(path, 'rb') as stream:
                    initial_contents = stream.read()

                yield path, initial_contents
            
def find_matches():
    found = set()
    for path, initial_contents in iter_files_in_dir(os.path.dirname(os.path.dirname(__file__))):
        found.update(find_matches_in_contents(initial_contents))
    print '\n'.join(sorted(found))
    print 'Total', len(found)
    
def make_replace():
    re_name_to_new_val = load_re_to_new_val()
    # traverse root directory, and list directories as dirs and files as files
    for path, initial_contents in iter_files_in_dir(os.path.dirname(os.path.dirname(__file__))):
        for key, val in re_name_to_new_val.iteritems():
            contents = re.sub(key, val, initial_contents)

        if contents != initial_contents:
            if re.findall(r'\b%s\b' % (val,), initial_contents):
                raise AssertionError('Error in:\n%s\n%s is already being used (and changes may conflict).' % (path, val,))
            
        with open(path, 'wb') as stream:
            stream.write(contents)


def load_re_to_new_val():
    name_to_new_val = {}
    for n in names_to_rename.NAMES.splitlines():
        n = n.strip()
        if not n.startswith('#') and n:
            name_to_new_val[r'\b'+n+r'\b'] = _normalize(n)
    return name_to_new_val

def test():
    assert _normalize('RestoreSysSetTraceFunc') == 'restore_sys_set_trace_func'
    assert _normalize('restoreSysSetTraceFunc') == 'restore_sys_set_trace_func'
    assert _normalize('Restore') == 'restore'
    matches = find_matches_in_contents('''
    def CamelCase()
    def camelCase()
    def ignore()
    def ignore_this()
    def Camel()
    def CamelCaseAnother()
    ''')
    assert matches == ['CamelCase', 'camelCase', 'Camel', 'CamelCaseAnother']
    
if __name__ == '__main__':
    #find_matches()
    make_replace()

