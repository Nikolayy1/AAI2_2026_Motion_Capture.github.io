import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DEFAULT_POSE_FILE = STATIC_DIR / "pose.npy"
DEFAULT_TRANS_FILE = STATIC_DIR / "trans.npy"
DEFAULT_BETAS_FILE = STATIC_DIR / "betas.npy"
DEFAULT_OUTPUT_FILE = STATIC_DIR / "opensim_animation.json"

BONE_TEMPLATE = {
    "pelvis": {"length": 0.4, "position": [0.0, 0.0, 0.0], "rotation_indices": [0, 1, 2]},
    "femur_r": {"length": 0.5, "position": [0.15, -0.25, 0.0], "rotation_indices": [3, 4, 5]},
    "tibia_r": {"length": 0.45, "position": [0.15, -0.6, 0.0], "rotation_indices": [6, 7, 8]},
    "talus_r": {"length": 0.1, "position": [0.15, -0.9, 0.05], "rotation_indices": [9, 10, 11]},
    "femur_l": {"length": 0.5, "position": [-0.15, -0.25, 0.0], "rotation_indices": [12, 13, 14]},
    "tibia_l": {"length": 0.45, "position": [-0.15, -0.6, 0.0], "rotation_indices": [15, 16, 17]},
    "talus_l": {"length": 0.1, "position": [-0.15, -0.9, 0.05], "rotation_indices": [18, 19, 20]},
    "torso": {"length": 0.6, "position": [0.0, 0.3, 0.0], "rotation_indices": [21, 22, 23]},
    "humerus_r": {"length": 0.25, "position": [0.2, 0.25, 0.0], "rotation_indices": [24, 25, 26]},
    "radius_r": {"length": 0.22, "position": [0.35, 0.05, 0.0], "rotation_indices": [27, 28, 29]},
    "humerus_l": {"length": 0.25, "position": [-0.2, 0.25, 0.0], "rotation_indices": [30, 31, 32]},
    "radius_l": {"length": 0.22, "position": [-0.35, 0.05, 0.0], "rotation_indices": [33, 34, 35]},
    "head": {"length": 0.2, "position": [0.0, 0.9, 0.0], "rotation_indices": [36, 37, 38]},
}

JOINT_TEMPLATE = [
    {"name": "hip_r", "position": [0.15, -0.1, 0.0], "type": "ball"},
    {"name": "knee_r", "position": [0.15, -0.45, 0.0], "type": "hinge"},
    {"name": "ankle_r", "position": [0.15, -0.8, 0.0], "type": "hinge"},
    {"name": "hip_l", "position": [-0.15, -0.1, 0.0], "type": "ball"},
    {"name": "knee_l", "position": [-0.15, -0.45, 0.0], "type": "hinge"},
    {"name": "ankle_l", "position": [-0.15, -0.8, 0.0], "type": "hinge"},
    {"name": "lumbar", "position": [0.0, 0.1, 0.0], "type": "ball"},
    {"name": "shoulder_r", "position": [0.2, 0.25, 0.0], "type": "ball"},
    {"name": "elbow_r", "position": [0.35, 0.05, 0.0], "type": "hinge"},
    {"name": "wrist_r", "position": [0.45, -0.15, 0.0], "type": "hinge"},
    {"name": "shoulder_l", "position": [-0.2, 0.25, 0.0], "type": "ball"},
    {"name": "elbow_l", "position": [-0.35, 0.05, 0.0], "type": "hinge"},
    {"name": "wrist_l", "position": [-0.45, -0.15, 0.0], "type": "hinge"},
]

MUSCLE_TEMPLATE = [
    {
        "name": "quadriceps_r",
        "points": [[0.08, -0.1, 0.05], [0.12, -0.3, 0.03], [0.15, -0.5, 0.0]],
        "activated": True,
        "activation": 0.7,
    },
    {
        "name": "hamstrings_r",
        "points": [[0.18, -0.1, -0.05], [0.16, -0.3, -0.03], [0.15, -0.5, 0.0]],
        "activated": False,
        "activation": 0.3,
    },
    {
        "name": "quadriceps_l",
        "points": [[-0.08, -0.1, 0.05], [-0.12, -0.3, 0.03], [-0.15, -0.5, 0.0]],
        "activated": True,
        "activation": 0.7,
    },
    {
        "name": "hamstrings_l",
        "points": [[-0.18, -0.1, -0.05], [-0.16, -0.3, -0.03], [-0.15, -0.5, 0.0]],
        "activated": False,
        "activation": 0.3,
    },
]


def load_npy(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return np.load(path, allow_pickle=True)


def normalize_pose_vector(pose: np.ndarray, length: int) -> np.ndarray:
    flat = pose.flatten()
    if flat.size < length:
        padded = np.zeros(length, dtype=float)
        padded[: flat.size] = flat
        return padded
    return flat[:length]


def frame_for_pose_vector(
    pose: np.ndarray,
    trans: Optional[np.ndarray] = None,
    frame_index: int = 0,
) -> Dict[str, Any]:
    pose_vector = normalize_pose_vector(pose, 39)

    bones = []
    for name, template in BONE_TEMPLATE.items():
        rotation_indices = template["rotation_indices"]
        bones.append(
            {
                "name": name,
                "length": template["length"],
                "position": {
                    "x": float(template["position"][0]),
                    "y": float(template["position"][1]),
                    "z": float(template["position"][2]),
                },
                "rotation": {
                    "x": float(pose_vector[rotation_indices[0]]),
                    "y": float(pose_vector[rotation_indices[1]]),
                    "z": float(pose_vector[rotation_indices[2]]),
                },
            }
        )

    if trans is not None and trans.ndim >= 2 and frame_index < trans.shape[0]:
        pelvis_translation = trans[frame_index]
        pelvis_bone = next((b for b in bones if b["name"] == "pelvis"), None)
        if pelvis_bone is not None:
            pelvis_bone["position"] = {
                "x": float(pelvis_translation[0]),
                "y": float(pelvis_translation[1]),
                "z": float(pelvis_translation[2]) if pelvis_translation.size >= 3 else 0.0,
            }

    joints = [
        {"name": j["name"], "position": {"x": float(j["position"][0]), "y": float(j["position"][1]), "z": float(j["position"][2])}, "type": j["type"]}
        for j in JOINT_TEMPLATE
    ]

    muscles = [
        {
            "name": m["name"],
            "points": [
                {"x": float(p[0]), "y": float(p[1]), "z": float(p[2])} for p in m["points"]
            ],
            "activated": bool(m["activated"]),
            "activation": float(m["activation"]),
        }
        for m in MUSCLE_TEMPLATE
    ]

    return {"bones": bones, "joints": joints, "muscles": muscles}


def build_animation_frames(
    pose_data: np.ndarray,
    trans_data: Optional[np.ndarray] = None,
) -> List[Dict[str, Any]]:
    frames = []
    for i, pose in enumerate(pose_data):
        frames.append(frame_for_pose_vector(pose, trans=trans_data, frame_index=i))
    return frames


def save_animation_json(frames: List[Dict[str, Any]], output_path: Path, fps: int = 24) -> None:
    payload = {"frames": frames, "fps": fps}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Saved animation JSON to {output_path}")


def build_fastapi_example_json(output_path: Path) -> None:
    example_path = ROOT / "backend_animation_example.py"
    contents = f"""from fastapi import FastAPI
import json
from pathlib import Path

app = FastAPI()
ROOT = Path(__file__).resolve().parent
ANIMATION_FILE = ROOT / {json.dumps(str(output_path.name))}

@app.get('/opensim/animation')
def get_opensim_animation():
    with open(ANIMATION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
"""
    example_path.write_text(contents, encoding="utf-8")
    print(f"Created FastAPI example file: {example_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert pose.npy to a simplified OpenSim animation JSON file.")
    parser.add_argument("--pose", type=Path, default=DEFAULT_POSE_FILE, help="Path to pose.npy")
    parser.add_argument("--trans", type=Path, default=DEFAULT_TRANS_FILE, help="Path to trans.npy")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE, help="Output JSON file")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second for the output JSON")
    args = parser.parse_args()

    pose_data = load_npy(args.pose)
    print(f"Loaded pose data from {args.pose} with shape {pose_data.shape}")

    trans_data = None
    if args.trans.exists():
        try:
            trans_data = load_npy(args.trans)
            print(f"Loaded trans data from {args.trans} with shape {trans_data.shape}")
        except Exception as exc:
            print(f"Warning: Failed to load trans data: {exc}")

    frames = build_animation_frames(pose_data, trans_data)
    save_animation_json(frames, args.output, fps=args.fps)
    build_fastapi_example_json(args.output)


if __name__ == "__main__":
    main()
