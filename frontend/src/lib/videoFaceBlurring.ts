import {
	detectionsToFaceBoxes,
	drawBlurredFaces,
	type FaceBox,
	getFaceDetector,
} from "$lib/faceBlurring";
import type { FaceDetector } from "@mediapipe/tasks-vision";

type BlurProgressCallback = (progress: number) => void;

const DETECTION_INTERVAL_MS = 33;
const FACE_BOX_HOLD_MS = 250;
const RECORDING_MIME_TYPES = [
	"video/mp4;codecs=h264",
	"video/mp4",
	"video/webm;codecs=vp9",
	"video/webm;codecs=vp8",
	"video/webm",
];

export async function blurFacesInVideo(
	file: File,
	onProgress?: BlurProgressCallback,
) {
	if (!("MediaRecorder" in window)) {
		throw new Error("This browser cannot record processed videos.");
	}

	const mimeType = getSupportedMimeType();

	if (!mimeType) {
		throw new Error("This browser does not support a usable video recorder.");
	}

	const objectUrl = URL.createObjectURL(file);
	const video = document.createElement("video");
	const canvas = document.createElement("canvas");
	const context = canvas.getContext("2d");
	let detector: FaceDetector | null = null;

	if (!context) {
		URL.revokeObjectURL(objectUrl);
		throw new Error("Could not prepare the video processing canvas.");
	}

	try {
		video.src = objectUrl;
		video.muted = true;
		video.playsInline = true;
		video.preload = "auto";

		await waitForLoadedMetadata(video);

		canvas.width = video.videoWidth;
		canvas.height = video.videoHeight;

		detector = await getFaceDetector();
		const faceDetector = detector;
		const stream = canvas.captureStream(getFrameRate(video));
		const recorder = new MediaRecorder(stream, { mimeType });
		const chunks: Blob[] = [];

		recorder.addEventListener("dataavailable", (event) => {
			if (event.data.size > 0) {
				chunks.push(event.data);
			}
		});

		const recordingFinished = new Promise<void>((resolve, reject) => {
			recorder.addEventListener("stop", () => resolve(), { once: true });
			recorder.addEventListener(
				"error",
				() => reject(new Error("Face-blurred recording failed.")),
				{ once: true },
			);
		});

		let lastDetectionTime = -DETECTION_INTERVAL_MS;
		let faces: FaceBox[] = [];
		let lastFacesSeenAt = -FACE_BOX_HOLD_MS;
		let animationFrame = 0;

		const drawFrame = () => {
			context.drawImage(video, 0, 0, canvas.width, canvas.height);

			const timestamp = video.currentTime * 1000;
			if (timestamp - lastDetectionTime >= DETECTION_INTERVAL_MS) {
				const result = faceDetector.detectForVideo(video, timestamp);
				const detectedFaces = detectionsToFaceBoxes(result.detections);
				if (detectedFaces.length > 0) {
					faces = detectedFaces;
					lastFacesSeenAt = timestamp;
				} else if (timestamp - lastFacesSeenAt > FACE_BOX_HOLD_MS) {
					faces = [];
				}
				lastDetectionTime = timestamp;
			}

			drawBlurredFaces(context, video, faces, canvas.width, canvas.height);

			if (video.duration > 0) {
				onProgress?.(
					Math.min(99, Math.round((video.currentTime / video.duration) * 100)),
				);
			}

			if (!video.ended) {
				animationFrame = requestAnimationFrame(drawFrame);
			}
		};

		recorder.start();
		drawFrame();
		await video.play();
		await waitForEnded(video);
		cancelAnimationFrame(animationFrame);

		if (recorder.state !== "inactive") {
			recorder.stop();
		}

		await recordingFinished;
		onProgress?.(100);

		const blob = new Blob(chunks, { type: mimeType });
		return new File([blob], getBlurredFileName(file.name, mimeType), {
			type: mimeType,
		});
	} finally {
		video.removeAttribute("src");
		video.load();
		detector?.close();
		URL.revokeObjectURL(objectUrl);
	}
}

function getSupportedMimeType() {
	return RECORDING_MIME_TYPES.find((mimeType) =>
		MediaRecorder.isTypeSupported(mimeType),
	);
}

function getFrameRate(video: HTMLVideoElement) {
	return video.duration > 20 ? 24 : 30;
}

function getBlurredFileName(fileName: string, mimeType: string) {
	const extension = mimeType.includes("mp4") ? "mp4" : "webm";
	const baseName = fileName.replace(/\.[^.]+$/, "");

	return `${baseName}-face-blurred.${extension}`;
}

function waitForLoadedMetadata(video: HTMLVideoElement) {
	return new Promise<void>((resolve, reject) => {
		video.addEventListener("loadedmetadata", () => resolve(), { once: true });
		video.addEventListener(
			"error",
			() => reject(new Error("Could not load the selected video.")),
			{ once: true },
		);
	});
}

function waitForEnded(video: HTMLVideoElement) {
	return new Promise<void>((resolve, reject) => {
		video.addEventListener("ended", () => resolve(), { once: true });
		video.addEventListener(
			"error",
			() => reject(new Error("Video processing failed before upload.")),
			{ once: true },
		);
	});
}
