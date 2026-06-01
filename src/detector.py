import os
import cv2
import numpy as np

class SlideDetector:
    """A slide transition detector module that leverages OpenCV to extract slide images

    based on frame difference analysis.
    """

    def __init__(self, threshold: float = 15.0, min_slide_duration: float = 5.0) -> None:
        """Initialize the SlideDetector with sensitivity thresholds and duration cooldowns.

        Args:
            threshold: Mean Absolute Error threshold above which a frame is marked as a slide change.
            min_slide_duration: Cooldown duration in seconds between two slide transitions.
        """
        self.threshold = threshold
        self.min_slide_duration = min_slide_duration

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

        keyframes = []
        prev_frame = None
        last_transition_time = -self.min_slide_duration
        
        # Anti-ghosting variables (Optimized Feature 1 & 2)
        transition_pending = False
        pending_transition_time = 0.0

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
                    img_name = "slide_0.00.jpg"
                    img_path = os.path.abspath(os.path.join(output_img_dir, img_name))
                    cv2.imwrite(img_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    keyframes.append({"timestamp": 0.0, "image_path": img_path})
                    last_transition_time = 0.0
                continue

            diff = self._calculate_diff(prev_frame, frame)
            
            # 1. Check if we have a pending transition that has now stabilized (diff drops below threshold)
            if transition_pending and diff < self.threshold:
                # Ensure the stabilized frame is not a solid blank screen
                if np.std(frame) >= 5.0:
                    img_name = f"slide_{pending_transition_time:.2f}.jpg"
                    img_path = os.path.abspath(os.path.join(output_img_dir, img_name))
                    cv2.imwrite(img_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    keyframes.append({"timestamp": pending_transition_time, "image_path": img_path})
                    last_transition_time = pending_transition_time
                transition_pending = False

            # 2. Check for new transition trigger (MAE exceeds threshold and cooldown has passed)
            elif diff > self.threshold and (current_time - last_transition_time) >= self.min_slide_duration:
                # Flag transition pending, wait for next frame to stabilize to avoid blurry animations
                transition_pending = True
                pending_transition_time = current_time

            prev_frame = frame.copy()

        # Defensive final frame flush in case video ends on a pending transition
        if transition_pending and prev_frame is not None:
            if np.std(prev_frame) >= 5.0:
                img_name = f"slide_{pending_transition_time:.2f}.jpg"
                img_path = os.path.abspath(os.path.join(output_img_dir, img_name))
                cv2.imwrite(img_path, prev_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                keyframes.append({"timestamp": pending_transition_time, "image_path": img_path})
                last_transition_time = pending_transition_time

        # 3. Automatic tail-frame capture (Optimized Feature 3)
        # Append the final frame if it is distant enough from the last transition to protect tail slides
        final_frame_idx = total_frames - 1
        final_time = float(final_frame_idx) / fps if fps > 0.0 else float(final_frame_idx) / 30.0
        if final_frame_idx >= 0 and (final_time - last_transition_time) >= self.min_slide_duration:
            cap.set(cv2.CAP_PROP_POS_FRAMES, final_frame_idx)
            ret, frame = cap.read()
            if ret and np.std(frame) >= 5.0:
                img_name = f"slide_{final_time:.2f}.jpg"
                img_path = os.path.abspath(os.path.join(output_img_dir, img_name))
                cv2.imwrite(img_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                keyframes.append({"timestamp": final_time, "image_path": img_path})

        cap.release()
        return keyframes
