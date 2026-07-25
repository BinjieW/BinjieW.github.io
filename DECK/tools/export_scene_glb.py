"""Execute a Blender Python scene script and export its geometry as GLB.

Usage:
  blender --background --python export_scene_glb.py -- \
    --source /absolute/path/to/scene.py \
    --output /absolute/path/to/model.glb
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

import bpy


EXPORTABLE_TYPES = {"MESH", "CURVE", "SURFACE", "FONT", "META"}


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    runpy.run_path(str(args.source.resolve()), run_name="__main__")
    bpy.context.view_layer.update()

    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in bpy.context.scene.objects:
        if obj.type in EXPORTABLE_TYPES and not obj.hide_render:
            obj.select_set(True)
            selected.append(obj)

    if not selected:
        raise RuntimeError(f"No exportable geometry produced by {args.source}")

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
    print(f"Exported {len(selected)} objects to {args.output}")


if __name__ == "__main__":
    main()
