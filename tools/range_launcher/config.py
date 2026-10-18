"""Validate the editable range catalog and build subprocess argument arrays."""

import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Tuple


OPTION_TYPES = {"choice", "multi", "text", "bool", "integer"}


def _error(where: str, message: str) -> None:
    raise ValueError("{}: {}".format(where, message))


def _string(value: Any, where: str, allow_empty: bool = False) -> None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        _error(where, "expected {}string".format("a " if allow_empty else "a nonempty "))
    if "\x00" in value:
        _error(where, "NUL characters are not allowed")


def _strings(value: Any, where: str, nonempty: bool = False) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        _error(where, "expected {}list of strings".format("a nonempty " if nonempty else "a "))
    for index, token in enumerate(value):
        _string(token, "{}[{}]".format(where, index), allow_empty=True)


def _identified(entries: Any, where: str, nonempty: bool = False) -> List[Dict[str, Any]]:
    if not isinstance(entries, list) or (nonempty and not entries):
        _error(where, "expected {}list".format("a nonempty " if nonempty else "a "))
    seen = set()
    for index, entry in enumerate(entries):
        location = "{}[{}]".format(where, index)
        if not isinstance(entry, dict):
            _error(location, "expected an object")
        identifier = entry.get("id")
        _string(identifier, location + ".id")
        if identifier in seen:
            _error(location + ".id", "duplicate id {!r}".format(identifier))
        seen.add(identifier)
        _string(entry.get("label"), location + ".label")
    return entries


def _option_value(option: Dict[str, Any], value: Any, where: str, from_ui: bool = False) -> Any:
    """Validate values; only integer entry strings need UI normalization."""
    kind = option["type"]
    required = option.get("required", False)
    if kind == "bool":
        if not isinstance(value, bool):
            _error(where, "expected true or false")
        if required and not value:
            _error(where, "a required flag must be enabled")
    elif kind == "integer":
        if from_ui and isinstance(value, str):
            if value.strip() == "":
                value = None
            else:
                try:
                    value = int(value)
                except ValueError:
                    _error(where, "expected an integer")
        if value is None:
            if required:
                _error(where, "an integer is required")
            return None
        if type(value) is not int:
            _error(where, "expected an integer")
        if "min" in option and value < option["min"]:
            _error(where, "must be at least {}".format(option["min"]))
        if "max" in option and value > option["max"]:
            _error(where, "must be at most {}".format(option["max"]))
    elif kind == "multi":
        _strings(value, where)
        if required and not value:
            _error(where, "at least one choice is required")
        allowed = {choice["value"] for choice in option["choices"]}
        if len(set(value)) != len(value):
            _error(where, "duplicate selected choices")
        for selected in value:
            if selected not in allowed:
                _error(where, "unknown choice {!r}".format(selected))
    else:
        _string(value, where, allow_empty=True)
        if required and not value.strip():
            _error(where, "a value is required")
        if kind == "choice" and value:
            allowed = {choice["value"] for choice in option["choices"]}
            if value not in allowed:
                _error(where, "unknown choice {!r}".format(value))
    return value


def _validate_range(item: Dict[str, Any], where: str) -> None:
    for field in ("category", "description", "cwd"):
        _string(item.get(field), where + "." + field, allow_empty=field == "description")
    _strings(item.get("command"), where + ".command", nonempty=True)
    _string(item["command"][0], where + ".command[0]")
    profiles = _identified(item.get("profiles"), where + ".profiles", nonempty=True)
    profile_ids = {profile["id"] for profile in profiles}
    profile_labels = set()
    for profile in profiles:
        if profile["label"] in profile_labels:
            _error(where + ".profiles." + profile["id"] + ".label", "duplicate profile label {!r}".format(profile["label"]))
        profile_labels.add(profile["label"])
        _strings(profile.get("args"), where + ".profiles." + profile["id"] + ".args")
    default_profile = item.get("default_profile")
    _string(default_profile, where + ".default_profile")
    if default_profile not in profile_ids:
        _error(where + ".default_profile", "unknown profile {!r}".format(default_profile))
    options = _identified(item.get("options"), where + ".options")
    for option in options:
        location = where + ".options." + option["id"]
        kind = option.get("type")
        if not isinstance(kind, str) or kind not in OPTION_TYPES:
            _error(location + ".type", "expected one of {}".format(", ".join(sorted(OPTION_TYPES))))
        _string(option.get("flag"), location + ".flag")
        if "required" in option and not isinstance(option["required"], bool):
            _error(location + ".required", "expected true or false")
        if "clearable" in option and not isinstance(option["clearable"], bool):
            _error(location + ".clearable", "expected true or false")
        if "profiles" in option:
            _strings(option["profiles"], location + ".profiles")
            for profile_id in option["profiles"]:
                if profile_id not in profile_ids:
                    _error(location + ".profiles", "unknown profile {!r}".format(profile_id))
        if kind in ("choice", "multi"):
            choices = option.get("choices")
            if not isinstance(choices, list) or not choices:
                _error(location + ".choices", "expected a nonempty list")
            seen = set()
            seen_labels = set()
            for choice_index, choice in enumerate(choices):
                choice_location = location + ".choices[{}]".format(choice_index)
                if not isinstance(choice, dict):
                    _error(choice_location, "expected an object")
                _string(choice.get("value"), choice_location + ".value")
                _string(choice.get("label"), choice_location + ".label")
                if choice["value"] in seen:
                    _error(choice_location + ".value", "duplicate choice {!r}".format(choice["value"]))
                seen.add(choice["value"])
                if choice["label"] in seen_labels:
                    _error(choice_location + ".label", "duplicate choice label {!r}".format(choice["label"]))
                seen_labels.add(choice["label"])
        for bound in ("min", "max"):
            if bound in option:
                if kind != "integer" or type(option[bound]) is not int:
                    _error(location + "." + bound, "expected an integer bound on an integer option")
        if "min" in option and "max" in option and option["min"] > option["max"]:
            _error(location, "min must not exceed max")
        if "default" not in option:
            _error(location + ".default", "missing default value")
        _option_value(option, option["default"], location + ".default")


def validate_catalog(data: Dict[str, Any]) -> None:
    """Raise a field-specific ValueError for an invalid version-one catalog."""
    if not isinstance(data, dict):
        _error("catalog", "expected an object")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        _error("schema_version", "only schema version 1 is supported")
    for item in _identified(data.get("ranges"), "ranges"):
        _validate_range(item, "ranges." + item["id"])


def load_catalog(path: Path) -> Dict[str, Any]:
    """Read UTF-8 JSON (including an optional editor BOM) and validate it."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("{}: {}".format(path, exc)) from exc
    validate_catalog(data)
    return data


def save_catalog(path: Path, data: Dict[str, Any]) -> None:
    """Validate before writes, back up the previous JSON, then replace atomically."""
    validate_catalog(data)
    path = Path(path)
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=str(path.parent), prefix=path.name + ".", suffix=".tmp",
                                         delete=False) as stream:
            temporary_path = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            shutil.copy2(str(path), str(path.with_suffix(path.suffix + ".bak")))
        os.replace(str(temporary_path), str(path))
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def default_values(item: Dict[str, Any]) -> Dict[str, Any]:
    """Give each UI a separate copy of mutable option defaults."""
    return {option["id"]: copy.deepcopy(option["default"]) for option in item["options"]}


def option_is_clearable(option: Dict[str, Any]) -> bool:
    """Clear selections by default, while keeping the user's environment setup."""
    return option.get("clearable", option["type"] in ("bool", "multi"))


def restore_values(item: Dict[str, Any], saved: Any = None) -> Dict[str, Any]:
    """Restore known values, repairing empty or obsolete protected choices."""
    values = default_values(item)
    if isinstance(saved, dict):
        values.update({key: copy.deepcopy(value) for key, value in saved.items() if key in values})
    for option in item["options"]:
        if option_is_clearable(option):
            continue
        value = values[option["id"]]
        empty = value is None or isinstance(value, str) and not value.strip()
        obsolete_choice = option["type"] == "choice" and value not in [choice["value"] for choice in option["choices"]]
        if empty or obsolete_choice:
            values[option["id"]] = copy.deepcopy(option["default"])
    return values


def clear_values(item: Dict[str, Any], saved: Dict[str, Any]) -> Dict[str, Any]:
    """Clear every selectable field, including fields in inactive profiles."""
    values = restore_values(item, saved)
    for option in item["options"]:
        if option_is_clearable(option):
            kind = option["type"]
            values[option["id"]] = False if kind == "bool" else [] if kind == "multi" else ""
    return values


def build_command(item: Dict[str, Any], profile_id: str, values: Dict[str, Any],
                  repo_root: Path, python_executable: str = sys.executable) -> Tuple[List[str], Path]:
    """Return argv and cwd without quoting, shell parsing, or executable launch."""
    validate_catalog({"schema_version": 1, "ranges": [item]})
    profile = next((profile for profile in item["profiles"] if profile["id"] == profile_id), None)
    if profile is None:
        _error(item["id"], "unknown profile {!r}".format(profile_id))
    if not isinstance(values, dict):
        _error(item["id"] + ".values", "expected an object")
    root = Path(repo_root).resolve()
    replacements = {
        "{root}": str(root), "{python}": str(python_executable),
        "{powershell}": shutil.which("powershell.exe") or shutil.which("powershell") or "powershell.exe",
    }

    def expand(token: str) -> str:
        for placeholder, replacement in replacements.items():
            token = token.replace(placeholder, replacement)
        return token

    command = [expand(token) for token in item["command"] + profile["args"]]
    for option in item["options"]:
        if "profiles" in option and profile_id not in option["profiles"]:
            continue
        value = values[option["id"]] if option["id"] in values else option["default"]
        value = _option_value(option, value, item["id"] + ".options." + option["id"], from_ui=True)
        if option["type"] == "bool":
            if value:
                command.append(expand(option["flag"]))
        elif option["type"] == "multi":
            if value:
                command.append(expand(option["flag"]))
                command.extend(expand(selected) for selected in value)
        elif value is not None and value != "":
            command.extend([expand(option["flag"]), expand(str(value))])
    cwd = Path(expand(item["cwd"]))
    if not cwd.is_absolute():
        cwd = root / cwd
    return command, cwd.resolve()
