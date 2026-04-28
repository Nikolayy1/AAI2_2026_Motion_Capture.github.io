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
		const paddingX = face.width * 0.2;
		const paddingY = face.height * 0.25;
		const x = clamp(face.x - paddingX, 0, canvasWidth);
		const y = clamp(face.y - paddingY, 0, canvasHeight);
		const width = clamp(face.width + paddingX * 2, 0, canvasWidth - x);
		const height = clamp(face.height + paddingY * 2, 0, canvasHeight - y);
		const pixelWidth = Math.max(4, Math.round(width * 0.04));
		const pixelHeight = Math.max(4, Math.round(height * 0.04));
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
		context.filter = "blur(40px)";
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
		context.fillStyle = "rgba(255, 255, 255, 0.08)";
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
			minDetectionConfidence: 0.35,
		});
	} catch {
		return FaceDetector.createFromOptions(vision, {
			baseOptions: {
				modelAssetPath: FACE_DETECTOR_MODEL_PATH,
				delegate: "CPU",
			},
			runningMode: "VIDEO",
			minDetectionConfidence: 0.35,
		});
	}
}

function clamp(value: number, min: number, max: number) {
	return Math.min(Math.max(value, min), max);
}
