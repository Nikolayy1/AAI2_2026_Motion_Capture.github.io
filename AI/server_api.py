import os
import uuid
import shutil
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from wham_api_v1 import WHAM_API_V1 as WHAM_API

import pandas as pd
import cv2
import mediapipe as mp


def export_2d_keypoints_csv(video_path: str, out_csv: Path):
    mp_pose = mp.solutions.pose

    important = {
        "head": mp_pose.PoseLandmark.NOSE,
        "left_shoulder": mp_pose.PoseLandmark.LEFT_SHOULDER,
        "right_shoulder": mp_pose.PoseLandmark.RIGHT_SHOULDER,
        "left_elbow": mp_pose.PoseLandmark.LEFT_ELBOW,
        "right_elbow": mp_pose.PoseLandmark.RIGHT_ELBOW,
        "left_wrist": mp_pose.PoseLandmark.LEFT_WRIST,
        "right_wrist": mp_pose.PoseLandmark.RIGHT_WRIST,
        "left_hip": mp_pose.PoseLandmark.LEFT_HIP,
        "right_hip": mp_pose.PoseLandmark.RIGHT_HIP,
        "left_knee": mp_pose.PoseLandmark.LEFT_KNEE,
        "right_knee": mp_pose.PoseLandmark.RIGHT_KNEE,
        "left_ankle": mp_pose.PoseLandmark.LEFT_ANKLE,
        "right_ankle": mp_pose.PoseLandmark.RIGHT_ANKLE,
    }

    rows = []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        frame_idx = 0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result.pose_landmarks:
                lm = result.pose_landmarks.landmark

                for name, landmark_id in important.items():
                    p = lm[landmark_id.value]

                    rows.append(
                        {
                            "frame": frame_idx,
                            "joint": name,
                            "x": float(p.x * width),
                            "y": float(p.y * height),
                            "visibility": float(p.visibility),
                        }
                    )

            frame_idx += 1

    cap.release()

    pd.DataFrame(rows).to_csv(out_csv, index=False)


app = FastAPI(title="WHAM API")

model_lock = Lock()

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

wham_model = WHAM_API()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/download/{request_id}/{filename}")
def download_file(request_id: str, filename: str):
    allowed_files = {
        "output.mp4",
        "wham_results.pth",
        "tracking_results.pth",
        "slam_results.pth",
        "keypoints_2d.csv",
    }

    if filename not in allowed_files:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = OUTPUT_DIR / request_id / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    if filename.endswith(".mp4"):
        media_type = "video/mp4"
    elif filename.endswith(".csv"):
        media_type = "text/csv"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


@app.post("/process_video")
async def infer_video(
    file: UploadFile = File(...),
    run_global: bool = Form(False),
    visualize: bool = Form(True),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".avi", ".mkv"}:
        raise HTTPException(status_code=400, detail="Unsupported video format")

    request_id = Path(file.filename).stem
    input_path = UPLOAD_DIR / f"{request_id}{suffix}"
    output_dir = OUTPUT_DIR / request_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with model_lock:
            results, tracking_results, slam_results = wham_model(
                str(input_path),
                output_dir=str(output_dir),
                calib=None,
                run_global=run_global,
                visualize=visualize,
            )

        keypoints_csv = output_dir / "keypoints_2d.csv"
        export_2d_keypoints_csv(str(input_path), keypoints_csv)

        output_video = output_dir / "output.mp4"
        if not output_video.exists():
            raise HTTPException(status_code=500, detail="output.mp4 not found")

        return FileResponse(
            path=str(output_video),
            media_type="video/mp4",
            filename="output.mp4",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        try:
            file.file.close()
        except Exception:
            pass


@app.post("/infer_compare_slam")
async def infer_compare_slam(
    file: UploadFile = File(...),
    visualize: bool = Form(False),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp4", ".mov", ".avi", ".mkv"}:
        raise HTTPException(status_code=400, detail="Unsupported video format")

    request_id = str(uuid.uuid4())
    input_path = UPLOAD_DIR / f"{request_id}{suffix}"

    base_output_dir = OUTPUT_DIR / request_id
    with_slam_dir = base_output_dir / "with_slam"
    without_slam_dir = base_output_dir / "without_slam"

    with_slam_dir.mkdir(parents=True, exist_ok=True)
    without_slam_dir.mkdir(parents=True, exist_ok=True)

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with model_lock:
            results_with_slam, tracking_with_slam, slam_with_slam = wham_model(
                str(input_path),
                output_dir=str(with_slam_dir),
                calib=None,
                run_global=True,
                visualize=visualize,
            )

            results_without_slam, tracking_without_slam, slam_without_slam = wham_model(
                str(input_path),
                output_dir=str(without_slam_dir),
                calib=None,
                run_global=False,
                visualize=visualize,
            )

        export_2d_keypoints_csv(str(input_path), with_slam_dir / "keypoints_2d.csv")
        export_2d_keypoints_csv(str(input_path), without_slam_dir / "keypoints_2d.csv")

        return JSONResponse(
            {
                "request_id": request_id,
                "message": "Comparison completed",
                "runs": {
                    "with_slam": {
                        "files": {
                            "output_mp4": str(with_slam_dir / "output.mp4"),
                            "tracking_results": str(with_slam_dir / "tracking_results.pth"),
                            "slam_results": str(with_slam_dir / "slam_results.pth"),
                            "wham_results": str(with_slam_dir / "wham_results.pth"),
                            "keypoints_2d": str(with_slam_dir / "keypoints_2d.csv"),
                        },
                        "summary": {
                            "num_tracks": len(results_with_slam),
                            "run_global": True,
                        },
                    },
                    "without_slam": {
                        "files": {
                            "output_mp4": str(without_slam_dir / "output.mp4"),
                            "tracking_results": str(without_slam_dir / "tracking_results.pth"),
                            "slam_results": str(without_slam_dir / "slam_results.pth"),
                            "wham_results": str(without_slam_dir / "wham_results.pth"),
                            "keypoints_2d": str(without_slam_dir / "keypoints_2d.csv"),
                        },
                        "summary": {
                            "num_tracks": len(results_without_slam),
                            "run_global": False,
                        },
                    },
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        try:
            file.file.close()
        except Exception:
            pass