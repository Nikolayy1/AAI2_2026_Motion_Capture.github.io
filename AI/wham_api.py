# General imports
import os
import sys
import time
import colorsys
import argparse
import os.path as osp
from glob import glob
from collections import defaultdict

# Third-party imports
import cv2
import torch
import joblib
import imageio
import numpy as np
from smplx import SMPL
from loguru import logger

# Local imports
from configs.config import get_cfg_defaults
from lib.data.datasets import CustomDataset
from lib.models import build_network, build_body_model
from lib.models.preproc.detector import DetectionModel
from lib.models.preproc.extractor import FeatureExtractor
from lib.utils.transforms import matrix_to_axis_angle
from lib.utils.imutils import avg_preds

# Try to import SLAM model. This is for estimating the global camera motion. DPVO (Deep Patch Visial SLAM) https://arxiv.org/abs/2408.01654
try:
    from lib.models.preproc.slam import SLAMModel

    _run_global = True
except:
    logger.info("DPVO is not properly installed. Only estimate in local coordinates !")
    _run_global = False


# Set configs (from configs/yamls/demo.yaml)
def prepare_cfg():
    cfg = get_cfg_defaults()
    cfg.merge_from_file("configs/yamls/demo.yaml")
    return cfg


# Opens video file with OpenCV and extracts metadata such as fps, length, width and height.
def load_video(video):
    cap = cv2.VideoCapture(video)
    assert cap.isOpened(), f"Faild to load video file {video}"
    fps = cap.get(cv2.CAP_PROP_FPS)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width, height = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(
        cv2.CAP_PROP_FRAME_HEIGHT
    )

    return cap, fps, length, width, height


# Main API class for WHAM
class WHAM_API_V1(object):
    # Initialize configs, build the WHAM network, and initialize the pre-processing models (detection, feature extraction, and SLAM if available).
    def __init__(self):
        self.cfg = prepare_cfg()
        self.network = build_network(
            self.cfg,
            build_body_model(
                self.cfg.DEVICE, self.cfg.TRAIN.BATCH_SIZE * self.cfg.DATASET.SEQLEN
            ),
        )
        self.network.eval()
        self.detector = None
        self.extractor = None
        self.slam = None

    # Preprocess the video, torch.no_grad is used to reduce memory usage and speed up computations during inference.
    @torch.no_grad()
    def preprocessing(self, video, cap, fps, length, output_dir):
        # if preprocess already exists, load the data. Otherwise compute them.
        if not (
            osp.exists(osp.join(output_dir, "tracking_results.pth"))
            and osp.exists(osp.join(output_dir, "slam_results.pth"))
        ):
            # while loop to load video frames one by one and run person detection + tracking and SLAM
            while cap.isOpened():
                flag, img = cap.read()
                if not flag:
                    break

                # 2D detection and tracking
                self.detector.track(img, fps, length)

                # SLAM
                if self.slam is not None:
                    self.slam.track()

            # Convert the tracking results into clean final result structure.
            tracking_results = self.detector.process(fps)

            # if SLAM is available retun actual motion estimates, otherwise return dummy data with the same length as the video frames.
            if self.slam is not None:
                slam_results = self.slam.process()
            else:
                slam_results = np.zeros((length, 7))
                slam_results[:, 3] = 1.0  # Unit quaternion

            # Extract image features for each tracked person in each frame.
            # TODO: Merge this into the previous while loop with an online bbox smoothing.
            tracking_results = self.extractor.run(video, tracking_results)
            # Save the processed data
            joblib.dump(tracking_results, osp.join(output_dir, "tracking_results.pth"))
            joblib.dump(slam_results, osp.join(output_dir, "slam_results.pth"))

        # If the processed data already exists, load the processed data
        else:
            tracking_results = joblib.load(osp.join(output_dir, "tracking_results.pth"))
            slam_results = joblib.load(osp.join(output_dir, "slam_results.pth"))

        return tracking_results, slam_results

    # Run WHAM inference on the preprocessed data
    @torch.no_grad()
    def wham_inference(
        self, tracking_results, slam_results, width, height, fps, output_dir
    ):
        dataset = CustomDataset(
            self.cfg, tracking_results, slam_results, width, height, fps
        )

        results = defaultdict(dict)

        n_subjs = len(dataset)
        for subj in range(n_subjs):
            if self.cfg.FLIP_EVAL:
                flipped_batch = dataset.load_data(subj, True)
                (
                    _id,
                    x,
                    inits,
                    features,
                    mask,
                    init_root,
                    cam_angvel,
                    frame_id,
                    kwargs,
                ) = flipped_batch
                flipped_pred = self.network(
                    x,
                    inits,
                    features,
                    mask=mask,
                    init_root=init_root,
                    cam_angvel=cam_angvel,
                    return_y_up=True,
                    **kwargs,
                )

                batch = dataset.load_data(subj)
                (
                    _id,
                    x,
                    inits,
                    features,
                    mask,
                    init_root,
                    cam_angvel,
                    frame_id,
                    kwargs,
                ) = batch
                pred = self.network(
                    x,
                    inits,
                    features,
                    mask=mask,
                    init_root=init_root,
                    cam_angvel=cam_angvel,
                    return_y_up=True,
                    **kwargs,
                )

                flipped_pose = flipped_pred["pose"].squeeze(0)
                flipped_shape = flipped_pred["betas"].squeeze(0)
                pose = pred["pose"].squeeze(0)
                shape = pred["betas"].squeeze(0)

                flipped_pose = flipped_pose.reshape(-1, 24, 6)
                pose = pose.reshape(-1, 24, 6)

                avg_pose, avg_shape = avg_preds(
                    pose, shape, flipped_pose, flipped_shape
                )
                avg_pose = avg_pose.reshape(-1, 144)
                avg_contact = (
                    flipped_pred["contact"][..., [2, 3, 0, 1]] + pred["contact"]
                ) / 2

                self.network.pred_pose = avg_pose.view_as(self.network.pred_pose)
                self.network.pred_shape = avg_shape.view_as(self.network.pred_shape)
                self.network.pred_contact = avg_contact.view_as(
                    self.network.pred_contact
                )

                output = self.network.forward_smpl(**kwargs)
                pred = self.network.refine_trajectory(
                    output, cam_angvel, return_y_up=True
                )
            else:
                batch = dataset.load_data(subj)
                (
                    _id,
                    x,
                    inits,
                    features,
                    mask,
                    init_root,
                    cam_angvel,
                    frame_id,
                    kwargs,
                ) = batch

                pred = self.network(
                    x,
                    inits,
                    features,
                    mask=mask,
                    init_root=init_root,
                    cam_angvel=cam_angvel,
                    return_y_up=True,
                    **kwargs,
                )

            pred_body_pose = (
                matrix_to_axis_angle(pred["poses_body"]).cpu().numpy().reshape(-1, 69)
            )
            pred_root = (
                matrix_to_axis_angle(pred["poses_root_cam"])
                .cpu()
                .numpy()
                .reshape(-1, 3)
            )
            pred_root_world = (
                matrix_to_axis_angle(pred["poses_root_world"])
                .cpu()
                .numpy()
                .reshape(-1, 3)
            )

            pred_pose = np.concatenate((pred_root, pred_body_pose), axis=-1)
            pred_pose_world = np.concatenate((pred_root_world, pred_body_pose), axis=-1)
            pred_trans = (pred["trans_cam"] - self.network.output.offset).cpu().numpy()

            results[_id]["pose"] = pred_pose
            results[_id]["trans"] = pred_trans
            results[_id]["pose_world"] = pred_pose_world
            results[_id]["trans_world"] = pred["trans_world"].cpu().squeeze(0).numpy()
            results[_id]["betas"] = pred["betas"].cpu().squeeze(0).numpy()
            results[_id]["verts"] = (
                (pred["verts_cam"] + pred["trans_cam"].unsqueeze(1)).cpu().numpy()
            )
            results[_id]["frame_ids"] = frame_id

        joblib.dump(results, osp.join(output_dir, "wham_results.pth"))
        return results

    @torch.no_grad()
    def __call__(self, video, output_dir, calib=None, run_global=True, visualize=False):
        self.slam = None
        self.detector = DetectionModel(self.cfg.DEVICE.lower())
        self.extractor = FeatureExtractor(self.cfg.DEVICE.lower(), self.cfg.FLIP_EVAL)

        cap, fps, length, width, height = load_video(video)
        os.makedirs(output_dir, exist_ok=True)

        try:
            run_global = run_global and _run_global
            if run_global:
                self.slam = SLAMModel(video, output_dir, width, height, calib)

            tracking_results, slam_results = self.preprocessing(
                video, cap, fps, length, output_dir
            )
            results = self.wham_inference(
                tracking_results, slam_results, width, height, fps, output_dir
            )

            if visualize:
                from lib.vis.run_vis import run_vis_on_demo

                run_vis_on_demo(
                    self.cfg,
                    video,
                    results,
                    output_dir,
                    self.network.smpl,
                    vis_global=run_global,
                )

            return results, tracking_results, slam_results
        finally:
            cap.release()
