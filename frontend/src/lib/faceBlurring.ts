import {
	FaceDetector,
	FilesetResolver,
	type BoundingBox,
	type Detection,
} from "@mediapipe/tasks-vision";

const MEDIAPIPE_WASM_PATH = "/mediapipe/wasm";
const FACE_DETECTOR_MODEL_PATH =
	"/mediapipe/models/blaze_face_full_range.tflite";

export type FaceBox = {
	x: number;
	y: number;
	width: number;
	height: number;
};

const FACE_PADDING_X_RATIO = 0.4;
const FACE_PADDING_Y_RATIO = 0.55;
const MIN_FACE_PADDING_PX = 24;
const BLUR_STRENGTH_PX = 56;
const PIXELATION_RATIO = 0.028;

let visionPromise: ReturnType<typeof FilesetResolver.forVisionTasks> | null = null;

export function getFaceDetector() {
	return createFaceDetector();
}

export function detectionsToFaceBoxes(detections: Detection[]) {
	return detections
		.map((detection) => detection.boundingBox)
		.filter((box): box is BoundingBox => Boolean(box))
		.map((box) => ({
			x: box.originX,
			y: box.originY,
			width: box.width,
			height: box.height,
		}));
}

export function drawBlurredFaces(
	context: CanvasRenderingContext2D,
	source: CanvasImageSource,
	faces: FaceBox[],
	canvasWidth: number,
	canvasHeight: number,
) {
	for (const face of faces) {
		// Bias upward and outward to cover hairline, jawline, and small detector drift.
		const paddingX = Math.max(MIN_FACE_PADDING_PX, face.width * FACE_PADDING_X_RATIO);
		const paddingY = Math.max(MIN_FACE_PADDING_PX, face.height * FACE_PADDING_Y_RATIO);
		const x = clamp(face.x - paddingX, 0, canvasWidth);
		const y = clamp(face.y - paddingY, 0, canvasHeight);
		const width = clamp(face.width + paddingX * 2, 0, canvasWidth - x);
		const height = clamp(face.height + paddingY * 2, 0, canvasHeight - y);
		const pixelWidth = Math.max(4, Math.round(width * PIXELATION_RATIO));
		const pixelHeight = Math.max(4, Math.round(height * PIXELATION_RATIO));
		const pixelCanvas = document.createElement("canvas");
		const pixelContext = pixelCanvas.getContext("2d");

		if (!pixelContext) {
			continue;
		}

		pixelCanvas.width = pixelWidth;
		pixelCanvas.height = pixelHeight;
		pixelContext.imageSmoothingEnabled = false;
		pixelContext.drawImage(
			source,
			x,
			y,
			width,
			height,
			0,
			0,
			pixelWidth,
			pixelHeight,
		);

		context.save();
		context.imageSmoothingEnabled = false;
		context.filter = `blur(${BLUR_STRENGTH_PX}px)`;
		context.drawImage(
			pixelCanvas,
			0,
			0,
			pixelWidth,
			pixelHeight,
			x,
			y,
			width,
			height,
		);
		context.filter = "none";
		context.fillStyle = "rgba(24, 24, 24, 0.16)";
		context.fillRect(x, y, width, height);
		context.restore();
	}
}

async function createFaceDetector() {
	visionPromise ??= FilesetResolver.forVisionTasks(MEDIAPIPE_WASM_PATH);
	const vision = await visionPromise;

	try {
		return await FaceDetector.createFromOptions(vision, {
			baseOptions: {
				modelAssetPath: FACE_DETECTOR_MODEL_PATH,
				delegate: "GPU",
			},
			runningMode: "VIDEO",
			minDetectionConfidence: 0.25,
		});
	} catch {
		return FaceDetector.createFromOptions(vision, {
			baseOptions: {
				modelAssetPath: FACE_DETECTOR_MODEL_PATH,
				delegate: "CPU",
			},
			runningMode: "VIDEO",
			minDetectionConfidence: 0.25,
		});
	}
}

function clamp(value: number, min: number, max: number) {
	return Math.min(Math.max(value, min), max);
}
