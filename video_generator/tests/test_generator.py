import unittest
import os
import shutil
import sys # Added for potential print suppression, and path manipulation
import io # Added for print suppression

# Ensure the video_generator package is discoverable
# This adds the directory containing 'video_generator' to Python's path
# Useful if tests are run from the 'video_generator/tests' directory directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from video_generator import generator

# Helper to get path relative to this test file
TEST_DIR = os.path.dirname(__file__)
ASSETS_TEST_DIR = os.path.join(TEST_DIR, 'test_assets')
TEMP_OUTPUT_DIR = os.path.join(TEST_DIR, 'temp_output')


class TestGeneratorLogic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create dummy asset directories and files for testing
        os.makedirs(ASSETS_TEST_DIR, exist_ok=True)
        os.makedirs(os.path.join(ASSETS_TEST_DIR, 'backgrounds'), exist_ok=True)
        os.makedirs(os.path.join(ASSETS_TEST_DIR, 'music'), exist_ok=True)
        os.makedirs(TEMP_OUTPUT_DIR, exist_ok=True)

        with open(os.path.join(ASSETS_TEST_DIR, 'quotes.txt'), 'w') as f:
            f.write("Test quote 1\n")
            f.write("Test quote 2\n")

        # Create a dummy background image
        try:
            img = Image.new('RGB', (100, 100), color='red') # Small size for speed
            img.save(os.path.join(ASSETS_TEST_DIR, 'backgrounds', 'test_bg.png'))
        except Exception as e:
            print(f"Test setup: Could not create dummy background image: {e}")
            # raise # Optionally re-raise if this is critical for many tests

        # Create a dummy font file (empty, just for path testing if needed)
        cls.test_font_path = os.path.join(ASSETS_TEST_DIR, "dummy_font.ttf")
        try:
            open(cls.test_font_path, 'a').close()
        except Exception as e:
            print(f"Test setup: Could not create dummy font file: {e}")


    @classmethod
    def tearDownClass(cls):
        # Clean up dummy assets
        shutil.rmtree(ASSETS_TEST_DIR, ignore_errors=True)
        shutil.rmtree(TEMP_OUTPUT_DIR, ignore_errors=True)
        # Clean up any temp files created by generator directly in root or test dir
        if os.path.exists("temp_black_bg.png"): os.remove("temp_black_bg.png")
        # Find and remove temp audio files created by moviepy in the current directory (if any)
        for item in os.listdir("."): # Current directory is video_generator/tests/
            if item.startswith("temp-audio-") and item.endswith(".m4a"):
                try: os.remove(item)
                except Exception: pass
            if item.startswith("temp_black_bg_") and item.endswith(".png"): # Temp bgs from get_background_clip
                try: os.remove(item)
                except Exception: pass
        # Check parent directory as well, as moviepy might put temp files there if run from root
        parent_dir_items = []
        try:
            parent_dir_items = os.listdir(os.path.join(TEST_DIR, ".."))
        except FileNotFoundError: # if tests are in root, there's no ".." in the same context
            pass
        for item in parent_dir_items:
            if item.startswith("temp-audio-") and item.endswith(".m4a"):
                try: os.remove(os.path.join(TEST_DIR, "..", item))
                except Exception: pass
            if item.startswith("temp_black_bg_") and item.endswith(".png"):
                try: os.remove(os.path.join(TEST_DIR, "..", item))
                except Exception: pass


    def test_get_quotes_reads_file(self):
        quotes_file = os.path.join(ASSETS_TEST_DIR, 'quotes.txt')
        quotes = generator.get_quotes(quotes_file)
        self.assertEqual(len(quotes), 2)
        self.assertIn("Test quote 1", quotes)

    def test_get_quotes_handles_missing_file(self):
        quotes = generator.get_quotes("non_existent_quotes.txt")
        self.assertIn("This is a default quote.", quotes[0])

    def test_get_quotes_handles_empty_file(self):
        empty_quotes_file = os.path.join(ASSETS_TEST_DIR, 'empty_quotes.txt')
        with open(empty_quotes_file, 'w') as f:
            pass
        quotes = generator.get_quotes(empty_quotes_file)
        self.assertIn("No quotes found in file.", quotes[0])
        os.remove(empty_quotes_file)

    def test_create_quote_image_generates_image(self):
        text = "Hello, World!"
        img = generator.create_quote_image(text, image_size=(200, 100))
        self.assertIsNotNone(img)
        self.assertEqual(img.size, (200, 100))
        self.assertEqual(img.mode, 'RGBA')

    def test_create_quote_image_with_specific_font_fallback(self):
        text = "Font Test"
        img = generator.create_quote_image(text, font_path="non_existent_font.ttf", font_size=20) # Use smaller font for faster test
        self.assertIsNotNone(img)
        self.assertEqual(img.mode, 'RGBA')

        alpha_channel = img.getchannel('A')
        self.assertTrue(any(p > 0 for p in alpha_channel.getdata()), "Image alpha channel is completely transparent, font rendering might have failed silently.")


    def test_get_random_file(self):
        test_bg_dir = os.path.join(ASSETS_TEST_DIR, 'backgrounds')
        self.assertTrue(os.path.exists(os.path.join(test_bg_dir, 'test_bg.png')))

        random_file = generator.get_random_file(test_bg_dir, ['.png'])
        self.assertIsNotNone(random_file)
        self.assertTrue(random_file.endswith('test_bg.png'))

        random_file_none = generator.get_random_file(test_bg_dir, ['.mp4'])
        self.assertIsNone(random_file_none)

        random_file_none = generator.get_random_file("non_existent_dir")
        self.assertIsNone(random_file_none)

    def test_get_background_clip_fallback(self):
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        clip = None
        temp_bg_path_associated_with_clip = None
        try:
            clip = generator.get_background_clip(background_path="non_existent_bg.mp4", duration=0.1)
            self.assertIsNotNone(clip, "Fallback clip should not be None.")
            self.assertEqual(clip.w, generator.VIDEO_WIDTH)
            self.assertEqual(clip.h, generator.VIDEO_HEIGHT)
            self.assertEqual(clip.duration, 0.1)
            if hasattr(clip, 'temp_bg_path'):
                 temp_bg_path_associated_with_clip = clip.temp_bg_path
                 self.assertTrue(os.path.exists(temp_bg_path_associated_with_clip), "Temp background file (e.g. temp_black_bg_xxxx.png) should exist before clip is closed when fallback is used.")
        finally:
            if clip and hasattr(clip, 'close'):
                clip.close()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            if temp_bg_path_associated_with_clip and os.path.exists(temp_bg_path_associated_with_clip):
                try:
                    os.remove(temp_bg_path_associated_with_clip)
                except Exception as e:
                    print(f"Warning: Could not remove temp_bg_path_associated_with_clip '{temp_bg_path_associated_with_clip}': {e}")


    def test_generate_video_runs(self):
        test_output_file = os.path.join(TEMP_OUTPUT_DIR, "test_output_video.mp4")
        bg_path = os.path.join(ASSETS_TEST_DIR, 'backgrounds', 'test_bg.png')

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        generated_successfully = False
        try:
            generator.generate_video(
                quote_text="Test Video Generation",
                output_filename=test_output_file,
                duration_per_quote=0.2,
                background_path=bg_path,
                music_path=None,
                font_path=self.test_font_path,
                font_size=30
            )
            self.assertTrue(os.path.exists(test_output_file), "Video file was not created.")
            # Increased minimum size slightly to be safer for very short clips
            self.assertTrue(os.path.getsize(test_output_file) > 500, f"Video file is too small ({os.path.getsize(test_output_file)} bytes), likely empty or corrupt.")
            generated_successfully = True
        except Exception as e:
            captured_output = sys.stdout.getvalue()
            self.fail(f"generate_video failed: {e}\nOutput:\n{captured_output}")
        finally:
            sys.stdout = old_stdout
            if os.path.exists(test_output_file):
                try:
                    os.remove(test_output_file)
                except Exception as e_rem:
                    print(f"Warning: Could not remove test output file {test_output_file}: {e_rem}")

        if generated_successfully:
             found_temp_bg = False
             # Check current dir and one level up for temp files from moviepy/generator
             dirs_to_check = ["."]
             if os.path.basename(os.getcwd()) == "tests": # If CWD is tests dir
                 dirs_to_check.append("..")

             for check_dir in dirs_to_check:
                 if not os.path.isdir(check_dir): continue
                 for item in os.listdir(check_dir):
                     if item.startswith("temp_black_bg_") and item.endswith(".png"):
                         found_temp_bg = True
                         # Try to remove it here if found, as it's a leftover
                         try: os.remove(os.path.join(check_dir, item))
                         except: pass
                         break
                 if found_temp_bg: break
             self.assertFalse(found_temp_bg, "Temporary background file (temp_black_bg_xxxx.png) from generate_video was not cleaned up.")


if __name__ == '__main__':
    unittest.main()
