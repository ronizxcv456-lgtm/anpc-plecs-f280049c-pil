"""Fill local paths in the model template without changing control settings."""
from pathlib import Path
import argparse
import base64
import json
import re
import struct

ROOT = Path(__file__).resolve().parent.parent
MODELS = ("npc_converter", "anpc_parallel_droop")

def _fragment(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]

def _ccs_settings(text, path, token="@ANPC_CCS_DIR@"):
    pattern = re.compile(
        r'(?m)^([ \t]*CodeGenTargetSettings[ \t]+)("[^"\r\n]*"(?:\r?\n"[^"\r\n]*")*)')
    changed = 0
    def replace(match):
        nonlocal changed
        data = base64.b64decode("".join(re.findall(r'"([^"]*)"', match[2])))
        old = token.encode("utf-16-be")
        index = data.find(old)
        if index < 0:
            return match[0]
        if data.count(old) != 1 or data[index-4:index] != struct.pack(">I", len(old)):
            raise ValueError("Unexpected CCS path encoding in the model template.")
        new = path.encode("utf-16-be")
        data = data[:index-4] + struct.pack(">I", len(new)) + new + data[index+len(old):]
        changed += 1
        return match[1] + json.dumps(base64.b64encode(data).decode("ascii"))
    result = pattern.sub(replace, text)
    if changed != 1:
        raise ValueError("Expected exactly one CCS path placeholder.")
    return result

def prepare(root, force=False, model_name="npc_converter"):
    if model_name not in MODELS:
        raise ValueError("Unknown model: " + model_name)
    root = Path(root).resolve()
    model = root / "models" / (model_name + ".plecs")
    module = root / "anpc_gpio_module"
    output = root / "build" / (model_name + ".plecs")
    for name in ("anpc_gpio.lua", "anpc_gpio_api.h", "anpc_gpio_core.h",
                 "anpc_gpio_hal.inc", "sim_output.c"):
        if not (module / name).is_file():
            raise FileNotFoundError(module / name)
    if output.exists() and not force:
        raise FileExistsError("Prepared model already exists. Save your edits; use --force to replace it.")
    text = model.read_text(encoding="utf-8")
    paths = {
        "@ANPC_MODULE_PARAM@": "'" + module.as_posix().replace("'", "''") + "'",
        "@ANPC_HEADER@": (module / "anpc_gpio_core.h").as_posix(),
    }
    controller_count = 2 if model_name == "anpc_parallel_droop" else 1
    for token, path in paths.items():
        if text.count(token) != controller_count:
            raise ValueError("Unexpected number of path placeholders: " + token)
        text = text.replace(token, _fragment(path))
    for index in range(1, controller_count + 1):
        suffix = "_" + str(index) if controller_count == 2 else ""
        directory = root / "build/droop" / ("controller" + str(index)) if suffix else root / "build"
        token = "@ANPC_CODEGEN_DIR" + suffix + "@"
        if text.count(token) != 1:
            raise ValueError("Expected exactly one path placeholder: " + token)
        text = text.replace(token, _fragment((directory / "codegen").as_posix()))
        text = _ccs_settings(text, (directory / "ccs_project/280049/cg").as_posix(),
                             "@ANPC_CCS_DIR" + suffix + "@")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS, default="npc_converter",
                        help="Model to prepare; defaults to the single-inverter model.")
    parser.add_argument("--force", action="store_true", help="Replace an existing prepared model.")
    args = parser.parse_args()
    try:
        print(prepare(ROOT, force=args.force, model_name=args.model))
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        parser.exit(1, str(error) + "\n")
