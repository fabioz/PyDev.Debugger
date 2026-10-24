"""Regression coverage for bounded defaultdict display and real DAP handling."""

import collections
import json
import sys

import pytest

from _pydevd_bundle.pydevd_safe_repr import SafeRepr


class CountedValue:
    calls = 0

    def __repr__(self):
        type(self).calls += 1
        return "leaf"


def nested_values():
    value = collections.defaultdict(lambda: collections.defaultdict(list))
    for outer in "abcdef":
        for inner in "ghijk":
            value[outer][inner] = [CountedValue() for _ in range(100)]
    return value


@pytest.mark.parametrize("factory", [None, list, dict, set, tuple, int, float, str, bool, bytes, object, frozenset, len, lambda: []])
def test_defaultdict_small(factory):
    value = collections.defaultdict(factory, {"a": [1, 2]})
    assert SafeRepr()(value) == repr(value)
    assert value.default_factory is factory


def test_defaultdict_does_not_format_hidden_leaves():
    value = nested_values()
    CountedValue.calls = 0
    result = SafeRepr()(value)
    assert CountedValue.calls == 0
    assert result.startswith("defaultdict(<function ")
    assert "defaultdict(<class 'list'>" in result
    assert "[...]" in result
    assert len(value) == 6
    assert all(len(items) == 100 for inner in value.values() for items in inner.values())


def test_defaultdict_many_keys():
    value = collections.defaultdict(list, {i: CountedValue() for i in range(100)})
    CountedValue.calls = 0
    result = SafeRepr()(value)
    assert result.startswith("defaultdict(<class 'list'>, {")
    assert "..." in result
    assert CountedValue.calls < SafeRepr.maxcollection[0]
    assert len(value) == 100


@pytest.mark.parametrize("indirect", [False, True])
def test_defaultdict_recursive(indirect):
    value = collections.defaultdict(list)
    value["self"] = [value] if indirect else value
    result = SafeRepr()(value)
    assert result.startswith("defaultdict(<class 'list'>, ")
    assert "..." in result
    assert len(result) < 200


def test_defaultdict_custom_repr_and_factory_are_preserved():
    class Custom(collections.defaultdict):
        def __repr__(self):
            return "custom-defaultdict"

    class Factory:
        def __call__(self):
            pytest.fail("Formatting must not invoke the default factory")

        def __repr__(self):
            return "custom-factory"

    class Meta(type):
        def __repr__(cls):
            return "custom-metaclass"

    class CustomType(metaclass=Meta):
        pass

    for value in (Custom(list), collections.defaultdict(Factory(), {"a": 1}), collections.defaultdict(CustomType, {"a": 1})):
        assert SafeRepr()(value) == repr(value)


@pytest.mark.parametrize("attribute", ["raw_value", "convert_to_hex"])
def test_defaultdict_explicit_formats(attribute):
    value = collections.defaultdict(list, {"a": [16]})
    formatter = SafeRepr()
    setattr(formatter, attribute, True)
    assert formatter(value) == repr(value)


def frame_with_value(value):
    return sys._getframe()


@pytest.fixture
def real_debugger():
    # Instantiate the actual debugger without connecting, tracing, or starting a listener.
    from pydevd import PyDB

    debugger = PyDB(set_as_global=False)
    commands = []

    class OutputCollector:
        # Only the output transport is replaced. Request dispatch, queue entries,
        # resolution, representation, response construction and ID mapping are real.
        def add_command(self, command):
            commands.append(command)

    debugger.writer = OutputCollector()
    yield debugger, commands
    debugger.writer = None


def request_variables(debugger, commands, reference, seq, fmt=None, dap_id=False):
    from _pydevd_bundle._debug_adapter import pydevd_base_schema
    from _pydevd_bundle.pydevd_process_net_command_json import PyDevJsonCommandProcessor

    args = {"variablesReference": reference}
    if fmt is not None:
        args["format"] = fmt
    request = pydevd_base_schema.from_json(
        json.dumps({"type": "request", "seq": seq, "command": "variables", "arguments": args}),
        update_ids_from_dap=dap_id,
    )
    processor = PyDevJsonCommandProcessor(pydevd_base_schema.from_json)
    assert processor.on_variables_request(debugger, request) is None
    queue, _event = debugger.get_internal_queue_and_event("defaultdict-test")
    command = queue.get_nowait()
    command.do_it(debugger)
    assert queue.empty()
    response = json.loads(commands.pop()._as_bytes.decode("utf-8"))
    assert response["success"] is True
    assert response["request_seq"] == seq
    assert response["command"] == "variables"
    assert not commands
    return {entry["name"]: entry for entry in response["body"]["variables"]}


def test_defaultdict_variables_request_and_child_expansion(real_debugger):
    from _pydevd_bundle.pydevd_frame_utils import create_frames_list_from_frame

    debugger, commands = real_debugger
    value = nested_values()
    original_keys = tuple(value)
    original_factories = (value.default_factory, tuple(v.default_factory for v in value.values()))
    original_ids = tuple(id(item) for inner in value.values() for items in inner.values() for item in items)
    frame = frame_with_value(value)
    manager = debugger.suspended_frames_manager
    with manager.track_frames(debugger) as tracker:
        tracker.track("defaultdict-test", create_frames_list_from_frame(frame))
        CountedValue.calls = 0
        parent = request_variables(debugger, commands, id(frame), 1)["value"]
        assert CountedValue.calls == 0
        assert parent["type"] == "defaultdict"
        assert parent["evaluateName"] == "value"
        assert parent["value"].startswith("defaultdict(<function ")
        assert parent["variablesReference"] > 0
        children = request_variables(debugger, commands, parent["variablesReference"], 2, dap_id=True)
        assert CountedValue.calls <= 6 * 5 * (SafeRepr.maxcollection[1] - 1)
        child = children["'a'"]
        assert child["type"] == "defaultdict"
        assert child["evaluateName"] == "value['a']"
        assert child["variablesReference"] != parent["variablesReference"]
        grandchildren = request_variables(debugger, commands, child["variablesReference"], 3, dap_id=True)
        grandchild = grandchildren["'g'"]
        assert grandchild["type"] == "list"
        assert grandchild["evaluateName"] == "value['a']['g']"
        leaves = request_variables(debugger, commands, grandchild["variablesReference"], 4, dap_id=True)
        first_leaf = next(entry for entry in leaves.values() if entry.get("evaluateName") == "value['a']['g'][0]")
        assert first_leaf["value"] == "leaf"
    assert manager.get_thread_id_for_variable_reference(id(frame)) is None
    assert tuple(value) == original_keys
    assert (value.default_factory, tuple(v.default_factory for v in value.values())) == original_factories
    assert tuple(id(item) for inner in value.values() for items in inner.values() for item in items) == original_ids


@pytest.mark.parametrize("fmt", [{"hex": True}, {"rawString": True}])
def test_defaultdict_request_format_propagation(real_debugger, fmt):
    from _pydevd_bundle.pydevd_frame_utils import create_frames_list_from_frame

    debugger, commands = real_debugger
    value = collections.defaultdict(list, {"a": [16]})
    frame = frame_with_value(value)
    with debugger.suspended_frames_manager.track_frames(debugger) as tracker:
        tracker.track("defaultdict-test", create_frames_list_from_frame(frame))
        entry = request_variables(debugger, commands, id(frame), 1, fmt=fmt)["value"]
        assert entry["value"] == repr(value)
        assert entry["type"] == "defaultdict"
        assert entry["variablesReference"] > 0


def test_defaultdict_presentation_provider_precedes_safe_repr(real_debugger, monkeypatch):
    from _pydevd_bundle import pydevd_xml
    from _pydevd_bundle.pydevd_extension_api import StrPresentationProvider
    from _pydevd_bundle.pydevd_frame_utils import create_frames_list_from_frame

    class Provider(StrPresentationProvider):
        def can_provide(self, type_object, type_name):
            return type_object is collections.defaultdict

        def get_str(self, value):
            return "provider-defaultdict"

        def get_str_in_context(self, value, context):
            return "provider-" + context

    handler = pydevd_xml._TYPE_RESOLVE_HANDLER
    if not handler._initialized:
        handler._initialize()
    monkeypatch.setattr(handler, "_str_providers", [Provider()])
    monkeypatch.setattr(handler, "_type_to_str_provider_cache", {})
    debugger, commands = real_debugger
    frame = frame_with_value(nested_values())
    with debugger.suspended_frames_manager.track_frames(debugger) as tracker:
        tracker.track("defaultdict-test", create_frames_list_from_frame(frame))
        CountedValue.calls = 0
        entry = request_variables(debugger, commands, id(frame), 1)["value"]
        assert entry["value"] == "provider-defaultdict"
        variable = debugger.suspended_frames_manager.get_variable(id(frame)).get_child_variable_named("value")
        assert variable.get_var_data(context="watch")["value"] == "provider-watch"
        assert CountedValue.calls == 0
