import bisect
from _pydevd_bundle.pydevd_constants import dict_items, NULL


class SourceMappingEntry(object):

    __slots__ = ['source_filename', 'line', 'end_line', 'runtime_line', 'runtime_source']

    def __init__(self, line, end_line, runtime_line, runtime_source):
        assert isinstance(runtime_source, str)

        self.line = int(line)
        self.end_line = int(end_line)
        self.runtime_line = int(runtime_line)
        self.runtime_source = runtime_source  # Something as <ipython-cell-xxx>
        self.source_filename = None  # Should be set after translated to server (absolute_normalized_source_filename).

    def contains_line(self, i):
        return self.line <= i <= self.end_line

    def contains_runtime_line(self, i):
        line_count = self.end_line + self.line
        runtime_end_line = self.runtime_line + line_count
        return self.runtime_line <= i <= runtime_end_line

    def __str__(self):
        return 'SourceMappingEntry(%s)' % (
            ', '.join('%s=%r' % (attr, getattr(self, attr)) for attr in self.__slots__))

    __repr__ = __str__


class _KeyifyList(object):

    def __init__(self, inner, key):
        self.inner = inner
        self.key = key

    def __len__(self):
        return len(self.inner)

    def __getitem__(self, k):
        return self.key(self.inner[k])


class SourceMapping(object):

    def __init__(self, on_source_mapping_changed=NULL):
        self._mappings_to_server = {}
        self._mappings_to_client = {}
        self._cache = {}
        self._on_source_mapping_changed = on_source_mapping_changed

    def set_source_mapping(self, absolute_normalized_source_filename, mapping):
        '''
        :param str absolute_normalized_source_filename:
            The filename for the source mapping (bytes on py2 and str on py3).
            Note: the absolute_normalized_source_filename must be already normalized to the server.

        :param list(SourceMappingEntry) mapping:
            A list with the source mapping entries to be applied to the given filename.

        :return str:
            An error message if it was not possible to set the mapping or an empty string if
            everything is ok.
        '''
        # Let's first validate if it's ok to apply that mapping.
        # File mappings must be 1:N, not M:N (i.e.: if there's a mapping from file1.py to <cell1>,
        # there can be no other mapping from any other file to <cell1>).
        # This is a limitation to make it easier to remove existing breakpoints when new breakpoints are
        # set to a file (so, any file matching that breakpoint can be removed instead of needing to check
        # which lines are corresponding to that file).
        for map_entry in mapping:
            existing_source_filename = self._mappings_to_client.get(map_entry.runtime_source)
            if existing_source_filename and existing_source_filename != absolute_normalized_source_filename:
                return 'Cannot apply mapping from %s to %s (it conflicts with mapping: %s to %s)' % (
                    absolute_normalized_source_filename, map_entry.runtime_source, existing_source_filename, map_entry.runtime_source)

        try:
            current_mapping = self._mappings_to_server.get(absolute_normalized_source_filename, [])
            for map_entry in current_mapping:
                del self._mappings_to_client[map_entry.runtime_source]

            self._mappings_to_server[absolute_normalized_source_filename] = sorted(mapping, key=lambda entry:entry.line)

            for map_entry in mapping:
                self._mappings_to_client[map_entry.runtime_source] = absolute_normalized_source_filename
        finally:
            self._cache.clear()
            self._on_source_mapping_changed()
        return ''

    def map_to_client(self, absolute_normalized_filename, lineno):
        key = (lineno, 'client', absolute_normalized_filename)
        try:
            return self._cache[key]
        except KeyError:
            for canonical_source_filename, mapping in dict_items(self._mappings_to_server):
                for map_entry in mapping:
                    if map_entry.runtime_source == absolute_normalized_filename:
                        if map_entry.contains_runtime_line(lineno):
                            self._cache[key] = (canonical_source_filename, map_entry.line + (lineno - map_entry.runtime_line), True)
                            return self._cache[key]

            self._cache[key] = (absolute_normalized_filename, lineno, False)
            return self._cache[key]

    def has_mapping_entry(self, absolute_normalized_filename):
        # Note that we're not interested in the line here, just on knowing if a given filename
        # (from the server) has a mapping for it.
        key = ('has_entry', absolute_normalized_filename)
        try:
            return self._cache[key]
        except KeyError:
            for _canonical_source_filename, mapping in dict_items(self._mappings_to_server):
                for map_entry in mapping:
                    if map_entry.runtime_source == absolute_normalized_filename:
                        self._cache[key] = True
                        return self._cache[key]

            self._cache[key] = False
            return self._cache[key]

    def map_to_server(self, absolute_normalized_filename, lineno):
        '''
        Convert something as 'file1.py' at line 10 to '<ipython-cell-xxx>' at line 2.

        Note that the name should be already normalized at this point.
        '''
        changed = False
        mappings = self._mappings_to_server.get(absolute_normalized_filename)
        if mappings:

            i = bisect.bisect(_KeyifyList(mappings, lambda entry:entry.line), lineno)
            if i >= len(mappings):
                i -= 1

            if i == 0:
                entry = mappings[i]

            elif i > 0:
                entry = mappings[i - 1]

            if not entry.contains_line(lineno):
                entry = mappings[i]
                if not entry.contains_line(lineno):
                    entry = None

            if entry is not None:
                lineno = entry.runtime_line + (lineno - entry.line)

                absolute_normalized_filename = entry.runtime_source
                changed = True

        return absolute_normalized_filename, lineno, changed

