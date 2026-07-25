"""Export one BlendNet JSONL entry to GLB.

Usage:
  blender --background --python export_blendnet_glb.py -- \
    --data /absolute/path/to/BlendNet.jsonl \
    --index 3 \
    --output /absolute/path/to/blendnet-birthday-cake.glb
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy


EXPORTABLE_TYPES = {"MESH", "CURVE", "SURFACE", "FONT", "META"}


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def load_entry(path: Path, index: int) -> dict:
    with path.open() as handle:
        for row_index, line in enumerate(handle):
            if row_index == index:
                return json.loads(line)
    raise IndexError(f"BlendNet index {index} not found in {path}")


def main() -> None:
    args = parse_args()
    entry = load_entry(args.data, args.index)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    exec(
        entry["script"],
        {"bpy": bpy, "math": math, "__builtins__": __builtins__},
    )
    bpy.context.view_layer.update()

    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in bpy.context.scene.objects:
        if obj.type in EXPORTABLE_TYPES and not obj.hide_render:
            obj.select_set(True)
            selected.append(obj)

    if not selected:
        raise RuntimeError(f"BlendNet entry {args.index} produced no geometry")

    bpy.context.view_layer.objects.active = selected[0]
    bpy.ops.export_scene.gltf(
        filepath=str(args.output.resolve()),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )
    print(
        f"Exported BlendNet[{args.index}] {entry.get('name', '')!r} "
        f"({len(selected)} objects) to {args.output}"
    )


if __name__ == "__main__":
    main()
