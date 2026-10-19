"""Check relocation, path encoding and protection of an edited local model."""
from pathlib import Path
import base64
import hashlib
import importlib.util
import re
import shutil
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("prepare_project", ROOT / "scripts/prepare_project.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ProjectTests(unittest.TestCase):
    def test_relocation_and_preserved_controls(self):
        template = ROOT / "models/npc_converter.plecs"
        original = template.read_text(encoding="utf-8")
        digest = hashlib.sha256(template.read_bytes()).digest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "ANPC 示例's clone"
            (root / "models").mkdir(parents=True)
            shutil.copyfile(template, root / "models/npc_converter.plecs")
            shutil.copytree(ROOT / "anpc_gpio_module", root / "anpc_gpio_module")
            output = module.prepare(root)
            text = output.read_text(encoding="utf-8")
            replacements = {
                "@ANPC_MODULE_PARAM@": "'" + (root / "anpc_gpio_module").as_posix().replace("'", "''") + "'",
                "@ANPC_HEADER@": (root / "anpc_gpio_module/anpc_gpio_core.h").as_posix(),
                "@ANPC_CODEGEN_DIR@": (root / "build/codegen").as_posix(),
            }
            expected = original
            for token, value in replacements.items():
                expected = expected.replace(token, module._fragment(value))
            expected = module._ccs_settings(expected, (root / "build/ccs_project/280049/cg").as_posix())
            self.assertEqual(text, expected)
            pattern = r'(?m)^[ \t]*CodeGenTargetSettings[ \t]+"([^"\r\n]+)"'
            blocks = [base64.b64decode(x) for x in re.findall(pattern, text)]
            encoded = (root / "build/ccs_project/280049/cg").as_posix().encode("utf-16-be")
            matches = [data for data in blocks if encoded in data]
            self.assertEqual(len(matches), 1)
            i = matches[0].index(encoded)
            self.assertEqual(matches[0][i-4:i], struct.pack(">I", len(encoded)))
            self.assertNotIn("@ANPC_", text)
            init_pattern = r"(?ms)InitializationCommands base64 (.*?)(?=^  InitialState)"
            self.assertEqual(re.search(init_pattern, text)[1], re.search(init_pattern, original)[1])
            output.write_text("local user edits", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                module.prepare(root)
            self.assertEqual(output.read_text(encoding="utf-8"), "local user edits")
            module.prepare(root, force=True)
            self.assertEqual(output.read_text(encoding="utf-8"), expected)
        self.assertEqual(hashlib.sha256(template.read_bytes()).digest(), digest)

if __name__ == "__main__":
    unittest.main()
