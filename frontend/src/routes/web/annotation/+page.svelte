<script>
  import { onMount } from "svelte";

  let video;
  let frames = $state([]);
  let frameIndex = $state(0);

  const width = 480;
  const height = 854;
  const fps = 59.00473933649289;

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

  onMount(async () => {
    const res = await fetch("/important_joints_2d.csv");
    const text = await res.text();
    frames = parseCSV(text);

    let rafId;

    function tick() {
      if (video && frames.length > 0 && !video.paused) {
        const videoFrame = Math.round(video.currentTime * fps);
        frameIndex = Math.min(videoFrame, frames.length - 1);
      }

      rafId = requestAnimationFrame(tick);
    }

    tick();

    return () => cancelAnimationFrame(rafId);
  });

  function parseCSV(text) {
    const rows = text.trim().split("\n").slice(1);
    const grouped = {};

    for (const row of rows) {
      const [frame, joint, x, y] = row.split(",");
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

  function project(p) {
    return {
      x: p.x,
      y: p.y,
    };
  }

  let dragging = $state(null);

  function startDrag(frame, joint) {
    dragging = { frame, joint };
  }

  function stopDrag() {
    dragging = null;
  }

  function dragPoint(event) {
    if (!dragging || !current) return;

    const svg = event.currentTarget;
    const rect = svg.getBoundingClientRect();

    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    frames[frameIndex].points[dragging.joint] = { x, y };
  }

  function setVideoToFrame(index) {
    if (!video || frames.length === 0) return;

    frameIndex = Math.max(0, Math.min(index, frames.length - 1));
    video.currentTime = frameIndex / fps;
  }

  function nextFrame() {
    video.pause();
    setVideoToFrame(frameIndex + 1);
  }

  function prevFrame() {
    video.pause();
    setVideoToFrame(frameIndex - 1);
  }

  function seekFrame(event) {
    video.pause();
    setVideoToFrame(Number(event.target.value));
  }

  function exportCSV() {
    if (!frames.length) return;

    let csv = "frame,joint,x,y\n";

    for (const f of frames) {
      for (const [joint, p] of Object.entries(f.points)) {
        csv += `${f.frame},${joint},${p.x},${p.y}\n`;
      }
    }

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "edited_keypoints.csv";
    a.click();

    URL.revokeObjectURL(url);
  }
</script>

<div style="position: relative; width: {width}px; height: {height}px;">
  <video
    bind:this={video}
    src="/original.mov"
    {width}
    {height}
    controls
    style="position:absolute; left:0; top:0;"
  />

  {#if current}
    <svg
      {width}
      {height}
      onpointermove={dragPoint}
      onpointerup={stopDrag}
      onpointerleave={stopDrag}
      style="position:absolute; left:0; top:0; pointer-events:none;"
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
          style="cursor: grab; pointer-events:auto;"
          onpointerdown={(e) => {
            e.stopPropagation();
            startDrag(current.frame, name);
          }}
        />
      {/each}
    </svg>
  {/if}
</div>

<p>Frame: {current?.frame ?? 0}</p>

<div style="margin-top: 12px; display: flex; gap: 8px; align-items: center;">
  <button onclick={prevFrame}>← 1 frame</button>

  <button onclick={() => (video.paused ? video.play() : video.pause())}>
    Play / Pause
  </button>

  <button onclick={nextFrame}>1 frame →</button>

  <input
    type="range"
    min="0"
    max={frames.length - 1}
    value={frameIndex}
    oninput={seekFrame}
    style="width: 300px;"
  />

  <span>
    Frame {frameIndex + 1} / {frames.length}
  </span>
</div>

<button onclick={exportCSV}> Save keypoints </button>
