<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { apiFetch } from "$lib/api";
  import { API_CONFIG } from "$lib/config";

  const params = new URLSearchParams(window.location.search);
  const videoUrl = params.get("video");
  const keypointsUrl = params.get("keypoints");

  type Point = {
    x: number;
    y: number;
  };

  type FrameData = {
    frame: number;
    points: Record<string, Point>;
  };

  type DragState = {
    frame: number;
    joint: string;
  };

  let video: HTMLVideoElement | null = null;
  let frames = $state<FrameData[]>([]);
  let frameIndex = $state(0);

  let width = $state(0);
  let height = $state(0);

  const connections = [
    ["head", "left_shoulder"],
    ["head", "right_shoulder"],
    ["left_shoulder", "right_shoulder"],
    ["left_shoulder", "left_elbow"],
    ["left_elbow", "left_wrist"],
    ["right_shoulder", "right_elbow"],
    ["right_elbow", "right_wrist"],
    ["left_shoulder", "left_hip"],
    ["right_shoulder", "right_hip"],
    ["left_hip", "right_hip"],
    ["left_hip", "left_knee"],
    ["left_knee", "left_ankle"],
    ["right_hip", "right_knee"],
    ["right_knee", "right_ankle"],
  ];

  let current = $derived(frames[frameIndex]);

  onMount(() => {
    let rafId = 0;

    function tick() {
      if (video && frames.length > 0 && !video.paused) {
        const videoFrame = Math.round(video.currentTime * fps);
        frameIndex = Math.min(videoFrame, frames.length - 1);
      }

      rafId = requestAnimationFrame(tick);
    }

    async function loadFrames() {
      if (!keypointsUrl) {
        console.error("Missing keypoints URL");
        return;
      }

      const res = await fetch(keypointsUrl);

      if (!res.ok) {
        console.error("Failed to load keypoints:", res.statusText);
        return;
      }

      const text = await res.text();
      frames = parseCSV(text);
      computeFPS();
    }

    void loadFrames();
    tick();

    return () => cancelAnimationFrame(rafId);
  });

  let fps = $state(30); // fallback

  function computeFPS() {
    if (!video || frames.length === 0) return;

    const totalFrames = frames.length;
    const duration = video.duration;

    if (duration > 0) {
      fps = totalFrames / duration;
      console.log("Computed FPS:", fps);
    }
  }

  function parseCSV(text: string): FrameData[] {
    const rows = text.trim().split("\n").slice(1);
    const grouped: Record<string, Record<string, Point>> = {};

    for (const row of rows) {
      const [frame, joint, x, y] = row.split(",");
      if (!frame || !joint || x === undefined || y === undefined) continue;
      if (!grouped[frame]) grouped[frame] = {};
      grouped[frame][joint] = {
        x: Number(x),
        y: Number(y),
      };
    }

    return Object.keys(grouped)
      .sort((a, b) => Number(a) - Number(b))
      .map((frame) => ({
        frame: Number(frame),
        points: grouped[frame],
      }));
  }

  function project(p: Point): Point {
    return {
      x: p.x,
      y: p.y,
    };
  }

  let dragging = $state<DragState | null>(null);

  function startDrag(frame: number, joint: string) {
    dragging = { frame, joint };
  }

  function stopDrag() {
    dragging = null;
  }

  function dragPoint(event: PointerEvent) {
    if (!dragging || !current) return;

    const svg = event.currentTarget as SVGSVGElement;
    const matrix = svg.getScreenCTM();

    if (!matrix) return;

    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;

    const svgPoint = point.matrixTransform(matrix.inverse());

    frames[frameIndex].points[dragging.joint] = {
      x: svgPoint.x,
      y: svgPoint.y,
    };
  }

  function setVideoToFrame(index: number) {
    if (!video || frames.length === 0) return;

    frameIndex = Math.max(0, Math.min(index, frames.length - 1));
    video.currentTime = frameIndex / fps;
  }

  function nextFrame() {
    if (!video) return;
    video.pause();
    setVideoToFrame(frameIndex + 1);
  }

  function prevFrame() {
    if (!video) return;
    video.pause();
    setVideoToFrame(frameIndex - 1);
  }

  function seekFrame(event: Event) {
    if (!video) return;
    const target = event.currentTarget as HTMLInputElement | null;
    if (!target) return;
    video.pause();
    setVideoToFrame(Number(target.value));
  }

  const submissionId = params.get("submission_id");

  async function exportCSV() {
    if (!frames.length || !submissionId) return;

    let csv = "frame,joint,x,y\n";

    for (const f of frames) {
      for (const [joint, p] of Object.entries(f.points)) {
        csv += `${f.frame},${joint},${p.x},${p.y}\n`;
      }
    }

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });

    const formData = new FormData();
    formData.append("file", blob, "corrected_keypoints_2d.csv");

    const res = await apiFetch(
      `${API_CONFIG.BASE_URL}/videos/${submissionId}/corrected-keypoints`,
      {
        method: "POST",
        body: formData,
      },
    );

    if (!res.ok) {
      alert("Failed to save corrected keypoints");
      return;
    }

    alert("Corrected keypoints saved");
  }

  function handleLoadedMetadata() {
    if (!video) return;

    width = video.videoWidth;
    height = video.videoHeight;

    computeFPS();
  }
</script>

<div class="page">
  <div class="topbar">
    <button
      class="back-btn"
      onclick={() => goto("/mobile/dashboard")}
      aria-label="Go back"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <polyline points="15 18 9 12 15 6"></polyline>
      </svg>
    </button>
    <span class="topbar-title">Annotation</span>
  </div>
  <div class="annotation-card">
    <h1>Keypoint Annotation</h1>

    <div class="video-stage">
      <video
        bind:this={video}
        src={videoUrl}
        controls
        onloadedmetadata={handleLoadedMetadata}
        class="video"
      ></video>

      {#if current && width && height}
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
          class="overlay"
          onpointermove={dragPoint}
          onpointerup={stopDrag}
          onpointerleave={stopDrag}
        >
          {#each connections as [a, b]}
            {#if current.points[a] && current.points[b]}
              {@const pa = project(current.points[a])}
              {@const pb = project(current.points[b])}

              <line
                x1={pa.x}
                y1={pa.y}
                x2={pb.x}
                y2={pb.y}
                stroke="lime"
                stroke-width="4"
              />
            {/if}
          {/each}

          {#each Object.entries(current.points) as [name, p]}
            {@const pos = project(p)}

            <circle
              cx={pos.x}
              cy={pos.y}
              r="8"
              fill="red"
              class="joint"
              onpointerdown={(e) => {
                e.stopPropagation();
                startDrag(current.frame, name);
              }}
            />
          {/each}
        </svg>
      {/if}
    </div>

    <p class="frame-label">Frame: {current?.frame ?? 0}</p>

    <div class="controls">
      <button onclick={prevFrame}>← 1 frame</button>

      <button onclick={() => (video?.paused ? video.play() : video?.pause())}>
        Play / Pause
      </button>

      <button onclick={nextFrame}>1 frame →</button>
    </div>

    <input
      class="slider"
      type="range"
      min="0"
      max={Math.max(frames.length - 1, 0)}
      value={frameIndex}
      oninput={seekFrame}
    />

    <p class="counter">Frame {frameIndex + 1} / {frames.length}</p>

    <button class="save-button" onclick={exportCSV}>Save keypoints</button>
  </div>
</div>

<style>
  .page {
    min-height: 100vh;
    background: #f5f8fa;
    padding: 32px;
    display: flex;
    justify-content: center;
  }

  .annotation-card {
    width: 100%;
    max-width: 1200px;
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  }

  h1 {
    margin: 0 0 18px;
    font-size: 22px;
    font-weight: 700;
    color: #222;
    text-align: center;
  }

  .video-stage {
    position: relative;
    width: 100%;
    max-width: 960px;
    height: 540px;
    background: #000;
    border-radius: 14px;
    overflow: hidden;
    margin: 0 auto;
  }

  .video {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: #000;
  }

  .overlay {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  .joint {
    cursor: grab;
    pointer-events: auto;
  }

  .frame-label,
  .counter {
    text-align: center;
    color: #555;
    font-size: 14px;
    margin: 12px 0;
  }

  .controls {
    display: flex;
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 14px;
  }

  .controls button,
  .save-button {
    border: none;
    border-radius: 10px;
    padding: 12px 14px;
    background: #e3f2fd;
    color: #1976d2;
    font-weight: 700;
    cursor: pointer;
  }

  .controls button:hover,
  .save-button:hover {
    background: #bbdefb;
  }

  .slider {
    width: 100%;
    margin-top: 16px;
    accent-color: #1976d2;
  }

  .save-button {
    width: 100%;
    margin-top: 12px;
    background: #90caf9;
    color: #000;
  }

  .topbar {
    position: absolute;
    top: 16px;
    left: 16px;
    right: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 10;
  }

  .back-btn {
    background: white;
    border: none;
    border-radius: 10px;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  .back-btn svg {
    width: 22px;
    height: 22px;
    color: #333;
  }

  .back-btn:hover {
    background: #f0f0f0;
  }

  .topbar-title {
    font-weight: 600;
    font-size: 16px;
    color: #333;
  }
</style>
