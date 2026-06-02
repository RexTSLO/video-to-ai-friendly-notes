import os
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

from src.detector import SlideDetector

def test_calculate_diff():
    """Test MAE calculating logic using mock numpy array frames."""
    detector = SlideDetector(threshold=15.0)

    # 1. Identical frames should have diff == 0
    frame_a = np.zeros((100, 100, 3), dtype=np.uint8)
    diff_same = detector._calculate_diff(frame_a, frame_a)
    assert diff_same == 0.0

    # 2. Fully distinct frames (0 vs 255) should have max MAE of 255
    frame_b = np.ones((100, 100, 3), dtype=np.uint8) * 255
    diff_diff = detector._calculate_diff(frame_a, frame_b)
    assert diff_diff == 255.0


def test_detect_slides_failure():
    """Test detect_slides raises ValueError if video fails to open."""
    detector = SlideDetector()
    with patch("cv2.VideoCapture") as mock_cap_class:
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = False
        mock_cap_class.return_value = mock_cap_instance

        with pytest.raises(ValueError) as exc_info:
            detector.detect_slides("invalid_path.mp4", "dummy_output")
        assert "Failed to open video" in str(exc_info.value)


def test_detect_slides_success(tmp_path):
    """Test successful slide change detection process with mocked video capture."""
    detector = SlideDetector(threshold=15.0, min_slide_duration=1.0)
    output_dir = str(tmp_path / "keyframes")

    with patch("cv2.VideoCapture") as mock_cap_class, \
         patch("cv2.imwrite") as mock_imwrite:

        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.side_effect = lambda prop: {
            5: 10.0,    # CAP_PROP_FPS
            7: 50       # CAP_PROP_FRAME_COUNT
        }.get(prop, 0.0)
        mock_cap_class.return_value = mock_cap_instance

        # We will trigger cap.read() 5 times (0, 10, 20, 30, 40)
        # Frame 0: Dark
        # Frame 10: Dark (No change)
        # Frame 20: White (Change!)
        # Frame 30: White (No change)
        # Frame 40: Dark (Change!)
        # Create simulated frames with rich structures to ensure standard deviation >= 5.0
        # and avoid getting filtered out by blank frame filters.
        np.random.seed(42)
        frame_dark = np.random.randint(10, 40, (100, 100, 3), dtype=np.uint8)
        frame_white = np.random.randint(210, 240, (100, 100, 3), dtype=np.uint8)

        # We can mock read() state using side_effect based on frame positioning
        current_frame_idx = [0]
        
        def mock_set(prop, val):
            if prop == 1: # CAP_PROP_POS_FRAMES
                current_frame_idx[0] = int(val)
            return True

        mock_cap_instance.set.side_effect = mock_set

        def mock_read():
            idx = current_frame_idx[0]
            if idx == 0 or idx == 10:
                return True, frame_dark
            elif idx == 20 or idx == 30:
                return True, frame_white
            elif idx == 40:
                return True, frame_dark
            return False, None

        mock_cap_instance.read.side_effect = mock_read
        mock_imwrite.return_value = True

        # Act
        keyframes = detector.detect_slides("dummy.mp4", output_dir)

        # Assert
        # Check detected slide timestamps:
        # - Frame 0 (0.0s): First frame ALWAYS captured.
        # - Frame 20 (2.0s): Dark to White (transition!).
        # - Frame 40 (4.0s): White to Dark (transition!).
        assert len(keyframes) == 3
        assert keyframes[0]["timestamp"] == 0.0
        assert keyframes[1]["timestamp"] == 2.0
        assert keyframes[2]["timestamp"] == 4.0

        # Check file save counts
        assert mock_imwrite.call_count == 3
        mock_cap_instance.release.assert_called_once()


def test_detect_slides_auto_threshold(tmp_path):
    """Test successful slide change detection process with auto thresholding."""
    detector = SlideDetector(threshold="auto", min_slide_duration=1.0)
    output_dir = str(tmp_path / "keyframes_auto")

    with patch("cv2.VideoCapture") as mock_cap_class, \
         patch("cv2.imwrite") as mock_imwrite:

        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.side_effect = lambda prop: {
            5: 10.0,    # CAP_PROP_FPS
            7: 50       # CAP_PROP_FRAME_COUNT
        }.get(prop, 0.0)
        mock_cap_class.return_value = mock_cap_instance

        np.random.seed(42)
        frame_dark = np.random.randint(10, 40, (100, 100, 3), dtype=np.uint8)
        frame_white = np.random.randint(210, 240, (100, 100, 3), dtype=np.uint8)

        current_frame_idx = [0]
        
        def mock_set(prop, val):
            if prop == 1: # CAP_PROP_POS_FRAMES
                current_frame_idx[0] = int(val)
            return True

        mock_cap_instance.set.side_effect = mock_set

        def mock_read():
            idx = current_frame_idx[0]
            if idx == 0 or idx == 10:
                return True, frame_dark
            elif idx == 20 or idx == 30:
                return True, frame_white
            elif idx == 40:
                return True, frame_dark
            return False, None

        mock_cap_instance.read.side_effect = mock_read
        mock_imwrite.return_value = True

        # Act
        keyframes = detector.detect_slides("dummy_auto.mp4", output_dir)

        # Assert
        assert len(keyframes) > 0
        assert mock_imwrite.call_count > 0
        mock_cap_instance.release.assert_called_once()


def test_consolidate_keyframes():
    """Test consolidate_keyframes method for first, final, and all modes."""
    # Create dark frame and slightly modified dark frames, and a white frame
    np.random.seed(42)
    # Use 160x90 frames as expected by consolidate_keyframes
    frame_0 = np.zeros((90, 160), dtype=np.uint8)
    frame_1 = np.ones((90, 160), dtype=np.uint8) * 2  # MAE difference = 2.0 (< 10.0)
    frame_2 = np.ones((90, 160), dtype=np.uint8) * 4  # MAE difference from frame_1 = 2.0 (< 10.0)
    frame_3 = np.ones((90, 160), dtype=np.uint8) * 255  # MAE difference = 251.0 (>= 10.0)

    # 1. Test "all" mode (should keep everything, pop temporary key, no deletion)
    detector_all = SlideDetector(slide_mode="all")
    keyframes_input = [
        {"timestamp": 0.0, "image_path": "slide_0.jpg", "frame_resized_gray": frame_0},
        {"timestamp": 2.0, "image_path": "slide_1.jpg", "frame_resized_gray": frame_1},
        {"timestamp": 4.0, "image_path": "slide_2.jpg", "frame_resized_gray": frame_2},
        {"timestamp": 6.0, "image_path": "slide_3.jpg", "frame_resized_gray": frame_3},
    ]
    
    with patch("os.path.exists") as mock_exists, \
         patch("os.remove") as mock_remove:
        mock_exists.return_value = True
        
        result_all = detector_all.consolidate_keyframes(keyframes_input)
        assert len(result_all) == 4
        # frame_resized_gray should be removed from all keyframes
        for kf in result_all:
            assert "frame_resized_gray" not in kf
        assert mock_remove.call_count == 0

    # 2. Test "final" mode (group 0, 1, 2 together -> keep 0 & 2, delete 1)
    detector_final = SlideDetector(slide_mode="final")
    keyframes_input = [
        {"timestamp": 0.0, "image_path": "slide_0.jpg", "frame_resized_gray": frame_0},
        {"timestamp": 2.0, "image_path": "slide_1.jpg", "frame_resized_gray": frame_1},
        {"timestamp": 4.0, "image_path": "slide_2.jpg", "frame_resized_gray": frame_2},
        {"timestamp": 6.0, "image_path": "slide_3.jpg", "frame_resized_gray": frame_3},
    ]
    
    with patch("os.path.exists") as mock_exists, \
         patch("os.remove") as mock_remove:
        mock_exists.return_value = True
        
        result_final = detector_final.consolidate_keyframes(keyframes_input)
        assert len(result_final) == 3
        # Keeps first (slide_0) and last (slide_2) of the group, and slide_3
        assert result_final[0]["timestamp"] == 0.0
        assert result_final[0]["image_path"] == "slide_0.jpg"
        assert result_final[1]["timestamp"] == 4.0
        assert result_final[1]["image_path"] == "slide_2.jpg"
        assert result_final[2]["timestamp"] == 6.0
        assert result_final[2]["image_path"] == "slide_3.jpg"
        
        # slide_1.jpg should be deleted
        assert mock_remove.call_count == 1
        deleted_paths = [call[0][0] for call in mock_remove.call_args_list]
        assert "slide_1.jpg" in deleted_paths
        assert "slide_0.jpg" not in deleted_paths
        assert "slide_2.jpg" not in deleted_paths

    # 3. Test "first" mode (group 0, 1, 2 together -> keep 0, timestamp remains 0.0, delete 1 & 2)
    detector_first = SlideDetector(slide_mode="first")
    keyframes_input = [
        {"timestamp": 0.0, "image_path": "slide_0.jpg", "frame_resized_gray": frame_0},
        {"timestamp": 2.0, "image_path": "slide_1.jpg", "frame_resized_gray": frame_1},
        {"timestamp": 4.0, "image_path": "slide_2.jpg", "frame_resized_gray": frame_2},
        {"timestamp": 6.0, "image_path": "slide_3.jpg", "frame_resized_gray": frame_3},
    ]
    
    with patch("os.path.exists") as mock_exists, \
         patch("os.remove") as mock_remove:
        mock_exists.return_value = True
        
        result_first = detector_first.consolidate_keyframes(keyframes_input)
        assert len(result_first) == 2
        assert result_first[0]["timestamp"] == 0.0
        assert result_first[0]["image_path"] == "slide_0.jpg"
        assert result_first[1]["timestamp"] == 6.0
        assert result_first[1]["image_path"] == "slide_3.jpg"
        
        # slide_1.jpg and slide_2.jpg should be deleted
        assert mock_remove.call_count == 2
        deleted_paths = [call[0][0] for call in mock_remove.call_args_list]
        assert "slide_1.jpg" in deleted_paths
        assert "slide_2.jpg" in deleted_paths
        assert "slide_0.jpg" not in deleted_paths

