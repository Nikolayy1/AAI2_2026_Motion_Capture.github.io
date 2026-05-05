<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { API_CONFIG } from "$lib/config";
  import { apiFetch } from "$lib/api";

  interface Video {
    filename: string;
    patient: string;
    exercise?: string;
    uploadDate?: string;
    duration?: string;
    thumbnail?: string;
    videoUrl?: string;
    keypointsUrl?: string;
    isAnnotated?: boolean;
    submissionId?: string;
  }

  let videos = $state<Video[]>([]);
  let isLoading = $state(true);
  let error = $state("");
  let searchQuery = $state("");
  let selectedExercise = $state("all");

  const exerciseTypes = [
    { value: "all", label: "All Exercises" },
    { value: "Sit-to-Stand", label: "Sit-to-Stand" },
    { value: "Balance Test", label: "Balance Test" },
    { value: "Walk Test", label: "Walk Test" },
    { value: "Gait Analysis", label: "Gait Analysis" },
    { value: "Range of Motion", label: "Range of Motion" },
  ];

  onMount(() => {
    void loadVideos();
  });

  async function loadVideos() {
    isLoading = true;
    error = "";

    try {
      const response = await apiFetch(API_CONFIG.VIDEO_LIST_ENDPOINT);

      if (!response.ok) {
        throw new Error(`Failed to load videos: ${response.statusText}`);
      }

      const data = await response.json();

      // Debug: Log the response to see what fields are available
      console.log("Backend response for all videos:", data);

      // Handle both response formats: {videos: [...]} or directly [...]
      const rawVideoList = Array.isArray(data) ? data : data.videos || [];
      const videoList = rawVideoList.filter((v: any) => v.annotated_video_url);

      if (videoList.length > 0) {
        console.log("First video data:", videoList[0]);
      }

      // Map backend response to frontend Video interface
      videos = videoList.map((v: any) => {
        // Try multiple possible field names for exercise type
        const exercise =
          v.exercise_type ||
          v.exerciseType ||
          v.exercise ||
          v.biometrics?.exercise_type ||
          v.metadata?.exercise_type ||
          "General";

        const filename =
          extractFilename(v.annotated_video_url) ||
          v.filename ||
          "video_out.mp4";
        const videoUrl = v.annotated_video_url;

        const videoData = {
          filename,
          patient: v.patient_name || v.patient?.name || "Unknown Patient",
          exercise,
          uploadDate:
            v.uploaded_at || v.upload_date || new Date().toISOString(),
          duration: v.duration || undefined,
          thumbnail: v.thumbnail || undefined,
          videoUrl,
          keypointsUrl: getKeypointsUrlFromVideoUrl(videoUrl),
          isAnnotated: true,
          submissionId: v.submission_id || undefined,
        };

        console.log(
          `Video ${v.submission_id || filename} - Exercise: ${exercise}, URL: ${videoUrl}, Annotated: ${videoData.isAnnotated}`,
        );

        return videoData;
      });

      // Thumbnail generation disabled due to CORS security restrictions
      // Videos will show placeholder icon instead
    } catch (err) {
      console.error("Error loading videos:", err);
      error = `${err}`;
      videos = [];
    } finally {
      isLoading = false;
    }
  }

  function extractFilename(url: string): string {
    if (!url) return "video.mp4";
    const parts = url.split("/");
    return parts[parts.length - 1] || "video.mp4";
  }

  async function generateThumbnail(
    videoUrl: string,
  ): Promise<string | undefined> {
    return new Promise((resolve) => {
      try {
        const video = document.createElement("video");
        const fullUrl = `${API_CONFIG.BASE_URL}${videoUrl}`;

        video.muted = true;
        video.preload = "metadata";

        let hasResolved = false;
        const resolveOnce = (value: string | undefined) => {
          if (!hasResolved) {
            hasResolved = true;
            resolve(value);
          }
        };

        video.onloadedmetadata = () => {
          const seekTime = Math.min(
            1,
            video.duration > 0 ? video.duration * 0.25 : 1,
          );
          video.currentTime = seekTime;
        };

        video.onseeked = () => {
          try {
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 360;

            const ctx = canvas.getContext("2d");
            if (ctx && video.videoWidth > 0 && video.videoHeight > 0) {
              ctx.drawImage(video, 0, 0);
              const thumbnailDataUrl = canvas.toDataURL("image/jpeg", 0.7);
              resolveOnce(thumbnailDataUrl);
            } else {
              resolveOnce(undefined);
            }
          } catch (err) {
            console.error("Error capturing video frame:", err);
            resolveOnce(undefined);
          }
        };

        video.onerror = (e) => {
          console.error("Error loading video for thumbnail:", e);
          resolveOnce(undefined);
        };

        video.src = fullUrl;
        video.load();

        setTimeout(() => resolveOnce(undefined), 10000);
      } catch (err) {
        console.error("Thumbnail generation error:", err);
        resolve(undefined);
      }
    });
  }

  function handleBack() {
    goto("/mobile/dashboard");
  }

  function handleUploadNew() {
    goto("/mobile/upload");
  }

  function getKeypointsUrlFromVideoUrl(videoUrl?: string) {
    if (!videoUrl) return undefined;

    return videoUrl.replace(/output\.mp4$/, "keypoints_2d.csv");
  }

  function handleAnnotationButton(event: MouseEvent, video: Video) {
    event.stopPropagation();

    const videoUrl = video.videoUrl?.startsWith("http")
      ? video.videoUrl
      : `${API_CONFIG.BASE_URL}${video.videoUrl}`;

    const keypointsUrl = video.keypointsUrl?.startsWith("http")
      ? video.keypointsUrl
      : `${API_CONFIG.BASE_URL}${video.keypointsUrl}`;

    goto(
      `/web/annotation?submission_id=${video.submissionId}&video=${encodeURIComponent(videoUrl)}&keypoints=${encodeURIComponent(keypointsUrl)}`,
    );
  }

  function handleVideoClick(video: Video) {
    if (!video.videoUrl) return;
    const videoUrl = video.videoUrl.startsWith("http")
      ? video.videoUrl
      : `${API_CONFIG.BASE_URL}${video.videoUrl}`;
    window.open(videoUrl, "_blank");
  }

  function formatDate(dateString?: string): string {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateString;
    }
  }

  // Filter videos based on search and exercise type
  let filteredVideos = $derived(() => {
    return videos.filter((video) => {
      const matchesSearch =
        searchQuery === "" ||
        video.patient.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (video.exercise?.toLowerCase().includes(searchQuery.toLowerCase()) ??
          false);

      const matchesExercise =
        selectedExercise === "all" || video.exercise === selectedExercise;

      return matchesSearch && matchesExercise;
    });
  });
</script>

<div class="container">
  <header>
    <button class="back-button" onclick={handleBack} aria-label="Go back">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path
          d="M15 18l-6-6 6-6"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>
    <h1>Video Library</h1>
  </header>

  <!-- Search and Filter -->
  <div class="controls">
    <div class="search-box">
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="search-icon"
      >
        <path
          d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM18 18l-4.35-4.35"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search by patient or exercise..."
        class="search-input"
      />
    </div>

    <select bind:value={selectedExercise} class="filter-select">
      {#each exerciseTypes as type}
        <option value={type.value}>{type.label}</option>
      {/each}
    </select>
  </div>

  <!-- Upload New Button -->
  <button class="upload-new-button" onclick={handleUploadNew}>
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
      <path
        d="M12 5v14M5 12h14"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
    Upload New Recording
  </button>

  <!-- Loading State -->
  {#if isLoading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading videos...</p>
    </div>
  {/if}

  <!-- Error State -->
  {#if error && !isLoading}
    <div class="error-state">
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="24" r="24" fill="#FFEBEE" />
        <path
          d="M24 16v8M24 28v2"
          stroke="#f44336"
          stroke-width="2"
          stroke-linecap="round"
        />
      </svg>
      <p class="error-message">{error}</p>
      <button class="retry-button" onclick={loadVideos}>Retry</button>
    </div>
  {/if}

  <!-- Videos List -->
  {#if !isLoading && !error}
    {#if filteredVideos().length === 0}
      <div class="empty-state">
        <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="32" fill="#E3F2FD" />
          <path d="M24 22l16 10-16 10V22z" fill="#64B5F6" />
        </svg>
        <h2>No Videos Found</h2>
        <p>
          {searchQuery || selectedExercise !== "all"
            ? "Try adjusting your filters"
            : "Upload your first recording to get started"}
        </p>
        <button class="upload-button" onclick={handleUploadNew}
          >Upload Recording</button
        >
      </div>
    {:else}
      <div class="video-grid">
        {#each filteredVideos() as video}
          <button
            type="button"
            class="video-card"
            onclick={() => handleVideoClick(video)}
          >
            <div class="video-thumbnail">
              {#if video.thumbnail}
                <img src={video.thumbnail} alt={video.filename} />
              {:else}
                <div class="thumbnail-placeholder">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <circle cx="24" cy="24" r="24" fill="white" opacity="0.3" />
                    <path d="M19 15l14 9-14 9V15z" fill="white" />
                  </svg>
                </div>
              {/if}
              {#if video.duration}
                <span class="duration-badge">{video.duration}</span>
              {/if}
            </div>
            <div class="video-info">
              <h3 class="video-title">{video.exercise || "General"}</h3>
              <p class="video-patient">{video.patient}</p>
              <div class="video-meta">
                <span class="video-date">{formatDate(video.uploadDate)}</span>
              </div>
            </div>
          </button>
          <button
            type="button"
            class="annotation-button"
            onclick={(e) => handleAnnotationButton(e, video)}
          >
            Annotate Keypoints
          </button>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .container {
    max-width: 430px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f5f8fa;
    min-height: 100vh;
  }

  header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
  }

  .back-button {
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #333;
    transition: color 0.2s;
  }

  .back-button:hover {
    color: #64b5f6;
  }

  h1 {
    font-size: 20px;
    font-weight: 600;
    color: #333;
    margin: 0;
  }

  /* Controls */
  .controls {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 16px;
  }

  .search-box {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-icon {
    position: absolute;
    left: 12px;
    color: #999;
  }

  .search-input {
    width: 100%;
    padding: 12px 12px 12px 44px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    color: #333;
    background-color: #ffffff;
    transition: border-color 0.2s;
    box-sizing: border-box;
  }

  .search-input:focus {
    outline: none;
    border-color: #64b5f6;
  }

  .search-input::placeholder {
    color: #999;
  }

  .filter-select {
    width: 100%;
    padding: 12px 16px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    color: #333;
    background-color: #ffffff;
    cursor: pointer;
    transition: border-color 0.2s;
  }

  .filter-select:focus {
    outline: none;
    border-color: #64b5f6;
  }

  /* Upload New Button */
  .upload-new-button {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: opacity 0.2s;
    margin-bottom: 24px;
  }

  .upload-new-button:hover {
    opacity: 0.9;
  }

  /* Loading State */
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 20px;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e0e0e0;
    border-top-color: #64b5f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .loading p {
    font-size: 14px;
    color: #666;
  }

  /* Error State */
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 20px;
  }

  .error-message {
    font-size: 14px;
    color: #f44336;
    margin: 16px 0;
    text-align: center;
  }

  .retry-button {
    padding: 10px 24px;
    background-color: #64b5f6;
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .retry-button:hover {
    opacity: 0.9;
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 20px;
    text-align: center;
  }

  .empty-state h2 {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    margin: 16px 0 8px 0;
  }

  .empty-state p {
    font-size: 14px;
    color: #666;
    margin-bottom: 24px;
  }

  .upload-button {
    padding: 12px 24px;
    background: linear-gradient(135deg, #64b5f6 0%, #42a5f5 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .upload-button:hover {
    opacity: 0.9;
  }

  /* Video Grid */
  .video-grid {
    display: grid;
    gap: 16px;
  }

  .video-card {
    border: none;
    background-color: #ffffff;
    border-radius: 12px;
    display: block;
    padding: 0;
    text-align: left;
    width: 100%;
    overflow: hidden;
    cursor: pointer;
    transition:
      transform 0.2s,
      box-shadow 0.2s;
  }

  .video-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .video-thumbnail {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    overflow: hidden;
  }

  .video-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .thumbnail-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .duration-badge {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
  }

  .video-info {
    padding: 16px;
  }

  .video-title {
    font-size: 16px;
    font-weight: 600;
    color: #333;
    margin: 0 0 4px 0;
  }

  .video-patient {
    font-size: 14px;
    color: #64b5f6;
    margin: 0 0 8px 0;
  }

  .video-meta {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .video-date {
    font-size: 12px;
    color: #999;
  }
</style>
