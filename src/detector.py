import os
import cv2
import numpy as np

class SlideDetector:
    """A slide transition detector module that leverages OpenCV to extract slide images

    based on frame difference analysis.
    """

    def __init__(self, threshold: float | str = "auto", min_slide_duration: float = 1.0, slide_mode: str = "final", skip_talking_heads: bool = False) -> None:
        """Initialize the SlideDetector with sensitivity thresholds and duration cooldowns.

        Args:
            threshold: Mean Absolute Error threshold above which a frame is marked as a slide change, or "auto".
            min_slide_duration: Cooldown duration in seconds between two slide transitions.
            slide_mode: Strategy for slide animations ("final", "all", "first").
            skip_talking_heads: Whether to skip duplicate speaker talking head frames.
        """
        self.threshold = threshold
        self.min_slide_duration = min_slide_duration
        self.slide_mode = slide_mode
        self.skip_talking_heads = skip_talking_heads

    def _calculate_diff(self, frame_a: np.ndarray, frame_b: np.ndarray) -> float:
        """Calculate the Mean Absolute Error (MAE) difference between two frames.

        Frames are converted to grayscale and downsized for rapid computational efficiency.

        Args:
            frame_a: The first RGB/BGR frame array.
            frame_b: The second RGB/BGR frame array.

        Returns:
            The MAE difference value between the frames.
        """
        gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

        # Resize to downscaled (160, 90) resolution for efficiency
        gray_a = cv2.resize(gray_a, (160, 90))
        gray_b = cv2.resize(gray_b, (160, 90))

        # Calculate mean absolute error (MAE)
        mae = np.mean(cv2.absdiff(gray_a, gray_b))
        return float(mae)

    def _get_resized_gray(self, frame: np.ndarray) -> np.ndarray:
        """Grayscale and downscale a frame to 160x90 for fast similarity comparison."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.resize(gray, (160, 90))

    def _get_face_detector(self, frame_width: int, frame_height: int):
        """Lazy initialization of the YuNet face detector, downloading model if missing."""
        if not hasattr(self, "_detector") or self._detector is None:
            model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, "face_detection_yunet_2023mar.onnx")

            if not os.path.exists(model_path):
                import urllib.request
                url = "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx"
                try:
                    print(f"[*] Downloading YuNet face detection model from {url}...")
                    urllib.request.urlretrieve(url, model_path)  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
                    print("[+] YuNet model downloaded successfully.")
                except Exception as e:
                    print(f"[-] WARNING: Failed to download YuNet model: {e}")
                    self._detector = None
                    return None

            try:
                self._detector = cv2.FaceDetectorYN.create(
                    model_path,
                    "",
                    (frame_width, frame_height),
                    0.8,
                    0.3,
                    5000
                )
                self._detector_size = (frame_width, frame_height)
            except Exception as e:
                print(f"[-] WARNING: Failed to initialize YuNet face detector: {e}")
                self._detector = None
                return None
        else:
            if self._detector_size != (frame_width, frame_height):
                try:
                    self._detector.setInputSize((frame_width, frame_height))
                    self._detector_size = (frame_width, frame_height)
                except Exception as e:
                    print(f"[-] WARNING: Failed to update YuNet input size: {e}")
                    return None

        return self._detector

    def _is_talking_head_frame(self, frame: np.ndarray) -> bool:
        """Detect if the frame represents a talking head (speaker face) rather than a slide.

        Uses YuNet to detect faces. If any face area is larger than 5% of the frame area,
        it is considered a talking head.
        """
        if not self.skip_talking_heads:
            return False

        h, w = frame.shape[:2]
        detector = self._get_face_detector(w, h)
        if detector is None:
            return False

        try:
            retval, faces = detector.detect(frame)
            if retval and faces is not None:
                frame_area = w * h
                for face in faces:
                    face_w = face[2]
                    face_h = face[3]
                    face_area = face_w * face_h
                    if (face_area / frame_area) >= 0.01:
                        return True
        except Exception as e:
            # Silently fallback to False on detection failure
            pass

        return False

    def _save_keyframe(self, frame: np.ndarray, timestamp: float, output_img_dir: str, keyframes: list[dict]) -> None:
        """Helper to write keyframe to disk and append to keyframes list."""
        img_name = f"slide_{timestamp:.2f}.jpg"
        img_path = os.path.abspath(os.path.join(output_img_dir, img_name))
        cv2.imwrite(img_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        keyframes.append({
            "timestamp": timestamp,
            "image_path": img_path,
            "frame_resized_gray": self._get_resized_gray(frame)
        })


    def consolidate_keyframes(self, keyframes: list[dict], similarity_threshold: float = 10.0) -> list[dict]:
        """Consolidate adjacent slide builds (animations) depending on self.slide_mode.

        Args:
            keyframes: List of captured keyframe dictionaries containing "frame_resized_gray".
            similarity_threshold: MAE boundary below which two slides are grouped as same.

        Returns:
            A cleaned and consolidated list of keyframes.
        """
        if not keyframes or self.slide_mode == "all":
            # Strip temporary arrays from memory cleanly
            for kf in keyframes:
                kf.pop("frame_resized_gray", None)
            return keyframes

        consolidated = []
        i = 0
        n = len(keyframes)

        while i < n:
            group = [keyframes[i]]
            j = i + 1
            while j < n:
                frame_a = group[-1]["frame_resized_gray"]
                frame_b = keyframes[j]["frame_resized_gray"]
                mae = np.mean(cv2.absdiff(frame_a, frame_b))
                
                if mae < similarity_threshold:
                    group.append(keyframes[j])
                    j += 1
                else:
                    break

            if self.slide_mode == "final":
                if len(group) >= 2:
                    # Keep both the initial (first) and completed (last) frames of the animation build sequence
                    first_kf = group[0].copy()
                    last_kf = group[-1].copy()
                    consolidated.append(first_kf)
                    consolidated.append(last_kf)

                    # Cleanup only the intermediate middle build JPEGs from disk
                    for discarded in group[1:-1]:
                        if os.path.exists(discarded["image_path"]):
                            try:
                                os.remove(discarded["image_path"])
                            except Exception as e:
                                print(f"[-] WARNING: Failed to clean up intermediate slide build: {e}")
                else:
                    consolidated.append(group[0].copy())
            elif self.slide_mode == "first":
                # Only keep the first keyframe in the group
                target_kf = group[0].copy()
                consolidated.append(target_kf)

                # Cleanup intermediate animation build slide images from disk
                for discarded in group[1:]:
                    if os.path.exists(discarded["image_path"]):
                        try:
                            os.remove(discarded["image_path"])
                        except Exception as e:
                            print(f"[-] WARNING: Failed to clean up intermediate slide build: {e}")
            else:
                consolidated.extend(group)

            i = j

        # Final strip of the temporary arrays
        for kf in consolidated:
            kf.pop("frame_resized_gray", None)

        return consolidated

    def detect_slides(self, video_path: str, output_img_dir: str) -> list[dict]:
        """Detect slide transitions from a video and persist keyframes as JPEGs.

        Implements optimal anti-ghosting stabilized capture, blank frame filtering,
        and automatic final frame protection.

        Args:
            video_path: Absolute or relative path to the source video file.
            output_img_dir: Directory where captured keyframe images will be saved.

        Returns:
            A list of dictionary descriptors containing keyframe timestamp and image path.
            e.g., [{"timestamp": 0.0, "image_path": ".../slide_0.00.jpg"}]

        Raises:
            ValueError: If the video cannot be opened.
        """
        if not os.path.exists(output_img_dir):
            os.makedirs(output_img_dir)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Handle edge case where fps might be 0 or invalid
        sample_interval = int(round(fps)) if fps > 0.0 else 30

        # Determine the actual threshold value to use dynamically or statically
        if self.threshold == "auto":
            diffs = []
            prev_frame_profile = None
            # Pass 1: Quick profiling of consecutive frame differences at 1 FPS
            for frame_idx in range(0, total_frames, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break
                # Only use frames that aren't a solid blank screen to calculate background noise
                if np.std(frame) >= 5.0:
                    if prev_frame_profile is not None:
                        diff = self._calculate_diff(prev_frame_profile, frame)
                        diffs.append(diff)
                    prev_frame_profile = frame.copy()
            
            if diffs:
                median = float(np.median(diffs))
                mad = float(np.median(np.abs(np.array(diffs) - median)))
                # Using k = 6.0 as a highly stable standard for lecture outlier detection
                k = 6.0
                dynamic_threshold = median + k * mad
                # Apply boundary capping for maximum safety (min=1.0, max=25.0)
                threshold_val = float(np.clip(dynamic_threshold, 1.0, 25.0))
                print(f"[+] Calculated dynamic MAE threshold: {threshold_val:.2f} (median: {median:.2f}, mad: {mad:.2f})")
            else:
                threshold_val = 15.0  # fallback default
        else:
            try:
                threshold_val = float(self.threshold)
            except ValueError:
                threshold_val = 15.0  # fallback default

        keyframes = []
        prev_frame = None
        last_transition_time = -self.min_slide_duration
        
        # Anti-ghosting variables (Optimized Feature 1 & 2)
        transition_pending = False
        pending_transition_time = 0.0
        in_talking_head = False

        # Iterate through the video sampling at 1 frame per second interval
        for frame_idx in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break

            current_time = float(frame_idx) / fps if fps > 0.0 else float(frame_idx) / 30.0

            if prev_frame is None:
                # Force capture the first frame ONLY if it's not a solid blank/black screen (Optimized Feature 3)
                # Standard deviation < 5.0 indicates a single solid color screen (no content)
                if np.std(frame) >= 5.0:
                    prev_frame = frame.copy()
                    is_talking_head = self._is_talking_head_frame(frame)
                    self._save_keyframe(frame, 0.0, output_img_dir, keyframes)
                    last_transition_time = 0.0
                    in_talking_head = is_talking_head
                continue

            diff = self._calculate_diff(prev_frame, frame)
            
            # 1. Check if we have a pending transition that has now stabilized (diff drops below threshold)
            # Or if it has been pending for too long (>= 2.0 seconds), force capture it to prevent blocking
            if transition_pending and (diff < threshold_val or (current_time - pending_transition_time) >= 2.0):
                # Ensure the stabilized frame is not a solid blank screen
                if np.std(frame) >= 5.0:
                    is_talking_head = self._is_talking_head_frame(frame)
                    if is_talking_head:
                        if not in_talking_head:
                            self._save_keyframe(frame, pending_transition_time, output_img_dir, keyframes)
                            last_transition_time = pending_transition_time
                            in_talking_head = True
                    else:
                        self._save_keyframe(frame, pending_transition_time, output_img_dir, keyframes)
                        last_transition_time = pending_transition_time
                        in_talking_head = False
                transition_pending = False

            # 2. Check for new transition trigger (MAE exceeds threshold and cooldown has passed)
            elif not transition_pending and (current_time - last_transition_time) >= self.min_slide_duration:
                if in_talking_head:
                    # Check if we have exited the talking head state
                    is_talking_head = self._is_talking_head_frame(frame)
                    if not is_talking_head:
                        in_talking_head = False
                        if diff > threshold_val:
                            transition_pending = True
                            pending_transition_time = current_time
                else:
                    if diff > threshold_val:
                        # Flag transition pending, wait for next frame to stabilize to avoid blurry animations
                        transition_pending = True
                        pending_transition_time = current_time

            prev_frame = frame.copy()

        # Defensive final frame flush in case video ends on a pending transition
        if transition_pending and prev_frame is not None:
            if np.std(prev_frame) >= 5.0:
                is_talking_head = self._is_talking_head_frame(prev_frame)
                if is_talking_head:
                    if not in_talking_head:
                        self._save_keyframe(prev_frame, pending_transition_time, output_img_dir, keyframes)
                        last_transition_time = pending_transition_time
                        in_talking_head = True
                else:
                    self._save_keyframe(prev_frame, pending_transition_time, output_img_dir, keyframes)
                    last_transition_time = pending_transition_time
                    in_talking_head = False

        # 3. Automatic tail-frame capture (Optimized Feature 3)
        # Append the final frame if it is distant enough from the last transition to protect tail slides
        final_frame_idx = total_frames - 1
        final_time = float(final_frame_idx) / fps if fps > 0.0 else float(final_frame_idx) / 30.0
        if final_frame_idx >= 0 and (final_time - last_transition_time) >= self.min_slide_duration:
            cap.set(cv2.CAP_PROP_POS_FRAMES, final_frame_idx)
            ret, frame = cap.read()
            if ret and np.std(frame) >= 5.0:
                is_talking_head = self._is_talking_head_frame(frame)
                if not (in_talking_head and is_talking_head):
                    self._save_keyframe(frame, final_time, output_img_dir, keyframes)

        cap.release()
        return self.consolidate_keyframes(keyframes)
