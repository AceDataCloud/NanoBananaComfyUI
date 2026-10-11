"""ComfyUI-facing output shape and image decoding."""

import importlib.util
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "nano_comfy", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
nodes = sys.modules["nano_comfy.nodes"]


class NanoBananaNodeTests(unittest.TestCase):
    def test_all_dify_models_are_offered(self):
        offered = nodes.AceNanoBananaGenerate.INPUT_TYPES()["required"]["model"][0]
        self.assertEqual(len(offered), 9)
        self.assertIn("nano-banana-2.1", offered)
        self.assertIn("nano-banana-pro:official", offered)

    def test_generated_task_id_is_visible_without_claiming_image(self):
        with patch.object(nodes, "generate", return_value=("pending", "task-123", [], "trace-123")):
            value = nodes.AceNanoBananaGenerate().run("bird", "nano-banana-2-lite", "1:1", "1K", 1)
        self.assertEqual(value["result"], ("pending", "task-123", "[]", "trace-123"))
        self.assertIn("task-123", " ".join(value["ui"]["text"]))

    def test_load_image_returns_comfy_image_tensor(self):
        raw = BytesIO()
        Image.new("RGB", (3, 2), color=(255, 0, 0)).save(raw, format="PNG")
        with patch.object(nodes, "download_image", return_value=raw.getvalue()):
            image, = nodes.AceNanoBananaLoadImage().run("https://cdn.acedata2.cloud/a.png")
        self.assertEqual(tuple(image.shape), (1, 2, 3, 3))
        self.assertAlmostEqual(float(image[0, 0, 0, 0]), 1.0)
        self.assertAlmostEqual(float(image[0, 0, 0, 1]), 0.0)

    def test_load_images_batches_matching_dimensions(self):
        raw = BytesIO()
        Image.new("RGB", (2, 2), color=(0, 0, 255)).save(raw, format="PNG")
        with patch.object(nodes, "download_image", return_value=raw.getvalue()):
            images, = nodes.AceNanoBananaLoadImages().run(
                '["https://cdn.acedata2.cloud/a.png","https://cdn.acedata2.cloud/b.png"]'
            )
        self.assertEqual(tuple(images.shape), (2, 2, 2, 3))


if __name__ == "__main__":
    unittest.main()
