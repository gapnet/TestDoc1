# video_generator/generator.py
import os
import random
import argparse # Import argparse
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (VideoFileClip,
                            ImageClip,
                            AudioFileClip,
                            CompositeVideoClip,
                            concatenate_videoclips)
from moviepy.video.fx.all import resize

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, 'backgrounds')
MUSIC_DIR = os.path.join(ASSETS_DIR, 'music')
QUOTES_FILE = os.path.join(ASSETS_DIR, 'quotes.txt')
DEFAULT_FONT_PATH = "arial.ttf"
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 24

def get_random_file(directory, file_extensions=None):
    """Selects a random file from a directory.
    Optionally filters by a list of file extensions."""
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' not found.")
        return None

    files = os.listdir(directory)
    if file_extensions:
        files = [f for f in files if f.lower().endswith(tuple(ext.lower() for ext in file_extensions))] # ensure lowercase for comparison

    if not files:
        print(f"Error: No suitable files found in '{directory}'.")
        return None
    return os.path.join(directory, random.choice(files))

def get_background_clip(background_path=None, duration=10):
    """Loads a background image or video, resizes it, and sets its duration."""
    clip = None
    temp_bg_path_to_clean = None

    if background_path is None:
        background_path = get_random_file(BACKGROUNDS_DIR, ['.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png'])

    if not background_path or not os.path.exists(background_path):
        print(f"Warning: Background file '{background_path}' not found or not specified. Using fallback black background.")
        black_bg_pil = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color='black')
        # Use a unique temp name to avoid clashes if multiple fallbacks are somehow created
        temp_bg_path_to_clean = f"temp_black_bg_{random.randint(1000,9999)}.png"
        black_bg_pil.save(temp_bg_path_to_clean)
        clip = ImageClip(temp_bg_path_to_clean, duration=duration).set_fps(VIDEO_FPS)

    elif background_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        clip = ImageClip(background_path, duration=duration)
    elif background_path.lower().endswith(('.mp4', '.avi', '.mov')):
        clip = VideoFileClip(background_path, audio=False)
        if clip.duration < duration:
            clip = clip.loop(duration=duration)
        clip = clip.subclip(0, duration)
    else:
        print(f"Error: Unsupported background file format: {background_path}. Using fallback black background.")
        black_bg_pil = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color='black')
        temp_bg_path_to_clean = f"temp_black_bg_{random.randint(1000,9999)}.png"
        black_bg_pil.save(temp_bg_path_to_clean)
        clip = ImageClip(temp_bg_path_to_clean, duration=duration).set_fps(VIDEO_FPS)

    if clip:
        clip = clip.resize(newsize=(VIDEO_WIDTH, VIDEO_HEIGHT))
        clip = clip.set_fps(VIDEO_FPS)

    # Store the path of the temporary file if one was created, so it can be cleaned up
    if temp_bg_path_to_clean and clip:
        clip.temp_bg_path = temp_bg_path_to_clean
    elif temp_bg_path_to_clean and not clip: # Should not happen if logic is correct
        try: os.remove(temp_bg_path_to_clean) # Clean up if clip creation failed
        except Exception: pass

    return clip


def get_quotes(quote_file_path=QUOTES_FILE): # Renamed parameter for clarity
    """Reads quotes from a file. Expects one quote per line."""
    if not os.path.exists(quote_file_path):
        print(f"Warning: Quotes file '{quote_file_path}' not found. Using default quote.")
        return ["This is a default quote. Create assets/quotes.txt to add your own."]
    try:
        with open(quote_file_path, 'r', encoding='utf-8') as f:
            quotes = [line.strip() for line in f if line.strip()]
        return quotes if quotes else ["No quotes found in file. Add some to the specified quotes file."]
    except Exception as e:
        print(f"Error reading quotes file '{quote_file_path}': {e}")
        return ["Error reading quotes. Please check the specified quotes file."]

def create_quote_image(text, image_size=(VIDEO_WIDTH, VIDEO_HEIGHT), font_path=DEFAULT_FONT_PATH, font_size=70, text_color=(255, 255, 255, 220), bg_color=(0,0,0,0)):
    """Creates a transparent image with the given text."""
    img = Image.new('RGBA', image_size, bg_color)
    draw = ImageDraw.Draw(img)
    font = None

    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Warning: Font '{font_path}' not found. Trying 'arial.ttf'.")
        try:
            font = ImageFont.truetype("arial.ttf", font_size) # Try arial as a common fallback
        except IOError:
            print(f"Warning: Font 'arial.ttf' also not found. Using PIL's default font.")
            try:
                font = ImageFont.load_default()
                if hasattr(font, "getsize"): # old PIL
                    font_size = 20 # default font is small, try to make it larger if possible
                else: # modern Pillow, load_default might be better
                    # try to get a larger version of default if possible, though it's tricky
                    pass
                print("Using PIL's load_default() font. Consider installing 'arial.ttf' or specifying a valid font path for better results.")
            except Exception as e_font:
                print(f"Critical font error, even PIL default failed: {e_font}. Text rendering will likely fail.")
                # Draw a placeholder error message if possible
                try:
                    err_font = ImageFont.load_default() # Minimal possible font
                    draw.text((10,10), "Font Error", font=err_font, fill=(255,0,0,255))
                except: pass
                return img # Return image with error or blank

    if font is None: # Should be caught by above, but as a safeguard
        print("Critical: Font object is None. Cannot render text.")
        return img


    max_chars_per_line = 40
    lines = []
    if text and text.strip():
        words = text.split()
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= max_chars_per_line:
                current_line += (" " + word if current_line else word)
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
    else:
        lines = ["No text provided."]

    wrapped_text = "\n".join(lines)

    text_x, text_y = 10, 10
    spacing = 4 # Line spacing

    if hasattr(draw, 'textbbox') and hasattr(font, 'getbbox'): # Modern Pillow
        # anchor 'lt' (left-top) for bbox calculation, then adjust
        bbox = draw.textbbox((0,0), wrapped_text, font=font, spacing=spacing, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (image_size[0] - text_width) / 2
        text_y = (image_size[1] - text_height) / 2
    elif hasattr(draw, 'textsize'): # Older Pillow/PIL
        text_width, text_height = draw.textsize(wrapped_text, font=font, spacing=spacing)
        text_x = (image_size[0] - text_width) / 2
        text_y = (image_size[1] - text_height) / 2

    draw.text((text_x, text_y), wrapped_text, font=font, fill=text_color, spacing=spacing, align="center")

    return img


def get_music_clip(music_path=None):
    """Loads a music file as an AudioFileClip."""
    if music_path is None:
        music_path = get_random_file(MUSIC_DIR, ['.mp3', '.wav', '.ogg'])

    if not music_path or not os.path.exists(music_path):
        print(f"Warning: Music file '{music_path}' not found or not specified. No audio will be added.")
        return None
    try:
        return AudioFileClip(music_path)
    except Exception as e:
        print(f"Error loading audio file '{music_path}': {e}")
        return None

def generate_video(quote_text, output_filename="output.mp4", duration_per_quote=10,
                   background_path=None, music_path=None, font_path=DEFAULT_FONT_PATH, font_size=70):
    """Generates a single video clip with one quote."""
    print(f"Generating video for quote: '{quote_text[:50]}...'")

    bg_clip_resource = None
    quote_clip_resource = None
    audio_clip_resource = None
    final_clip_resource = None
    temp_bg_to_remove_on_exit = None

    try:
        bg_clip = get_background_clip(background_path, duration=duration_per_quote)
        if bg_clip is None: # Critical failure in background loading
            print("Error: Could not load or create a background clip. Aborting video generation.")
            return

        bg_clip_resource = bg_clip
        if hasattr(bg_clip, 'temp_bg_path'): # Check if a temp file was created by get_background_clip
            temp_bg_to_remove_on_exit = bg_clip.temp_bg_path


        if bg_clip.duration == 0 and duration_per_quote > 0:
            print("Warning: Background clip has zero duration. Setting to default duration.")
            bg_clip = bg_clip.set_duration(duration_per_quote)

        quote_img = create_quote_image(quote_text, font_path=font_path, font_size=font_size)
        quote_clip = ImageClip(quote_img).set_duration(duration_per_quote).set_position('center')
        quote_clip_resource = quote_clip

        audio_clip = get_music_clip(music_path)
        if audio_clip:
            audio_clip_resource = audio_clip

        final_clip = CompositeVideoClip([bg_clip, quote_clip], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        final_clip_resource = final_clip

        if audio_clip:
            if audio_clip.duration < final_clip.duration:
                audio_clip = audio_clip.loop(duration=final_clip.duration)
            final_clip = final_clip.set_audio(audio_clip.subclip(0, final_clip.duration))

        final_clip = final_clip.set_fps(VIDEO_FPS)

        print(f"Writing video to {output_filename}...")
        # Ensure temp_audiofile has a unique name to prevent issues if multiple runs happen quickly
        temp_audio_filename = f'temp-audio-{random.randint(1000,9999)}.m4a'
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio_filename, remove_temp=True, logger='bar')
        print("Video generated successfully!")

    except Exception as e:
        print(f"Error during video generation or writing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up resources
        for clip_resource in [bg_clip_resource, quote_clip_resource, audio_clip_resource, final_clip_resource]:
            if clip_resource and hasattr(clip_resource, 'close'):
                try: clip_resource.close()
                except Exception as e_close: print(f"Error closing clip: {e_close}")

        if temp_bg_to_remove_on_exit and os.path.exists(temp_bg_to_remove_on_exit):
            try: os.remove(temp_bg_to_remove_on_exit)
            except Exception as e_remove: print(f"Error removing temporary background file {temp_bg_to_remove_on_exit}: {e_remove}")


def main():
    # Setup for basic test run if assets are missing
    if not os.path.exists(ASSETS_DIR):
        try: os.makedirs(ASSETS_DIR)
        except Exception as e: print(f"Could not create ASSETS_DIR: {e}")
    if not os.path.exists(BACKGROUNDS_DIR):
        try: os.makedirs(BACKGROUNDS_DIR)
        except Exception as e: print(f"Could not create BACKGROUNDS_DIR: {e}")
    if not os.path.exists(MUSIC_DIR):
        try: os.makedirs(MUSIC_DIR)
        except Exception as e: print(f"Could not create MUSIC_DIR: {e}")

    # Check if BACKGROUNDS_DIR is empty or only contains non-media files (e.g. .DS_Store)
    bg_dir_files = []
    try: bg_dir_files = os.listdir(BACKGROUNDS_DIR)
    except Exception as e: print(f"Could not list BACKGROUNDS_DIR: {e}")

    if not any(f.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov')) for f in bg_dir_files):
        try:
            print("Creating dummy background as no valid media found in assets/backgrounds...")
            dummy_bg = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color='blue')
            dummy_bg.save(os.path.join(BACKGROUNDS_DIR, 'default_background.png'))
        except Exception as e:
            print(f"Could not create dummy background: {e}")

    if not os.path.exists(QUOTES_FILE) or (os.path.exists(QUOTES_FILE) and os.path.getsize(QUOTES_FILE) == 0):
        try:
            print("Creating dummy quotes file...")
            with open(QUOTES_FILE, 'w', encoding='utf-8') as f:
                f.write("This is a test quote from generator.py.\n")
                f.write("Another quote for testing purposes.\n")
        except Exception as e:
            print(f"Could not create dummy quotes file: {e}")

    parser = argparse.ArgumentParser(description="Generate a YouTube video with a quote, background, and lofi music.")
    parser.add_argument('--quote', type=str, help="A single quote string to display.")
    parser.add_argument('--quote_file', type=str, default=QUOTES_FILE, help=f"Path to a text file containing quotes (one per line). Defaults to {QUOTES_FILE}")
    parser.add_argument('--music_path', type=str, help="Path to a specific music file. If not provided, a random one from assets/music will be chosen.")
    parser.add_argument('--background_path', type=str, help="Path to a specific background image or video. If not provided, a random one from assets/backgrounds will be chosen.")
    parser.add_argument('--output_filename', type=str, default="output.mp4", help="Filename for the output video. Default: output.mp4")
    parser.add_argument('--duration', type=int, default=10, help="Duration of the video for the quote in seconds. Default: 10s")
    parser.add_argument('--font_path', type=str, default=DEFAULT_FONT_PATH, help=f"Path to the .ttf font file. Default: {DEFAULT_FONT_PATH} (Ensure this font is available or in system path)")
    parser.add_argument('--font_size', type=int, default=80, help="Font size for the quote. Default: 80")

    args = parser.parse_args()

    quote_to_use = None
    if args.quote:
        quote_to_use = args.quote
    else:
        # Use args.quote_file which defaults to QUOTES_FILE if not provided by user
        quotes_from_file = get_quotes(args.quote_file)
        if quotes_from_file and quotes_from_file[0] != "This is a default quote. Create assets/quotes.txt to add your own." and not quotes_from_file[0].startswith("Error reading quotes"): # check if actual quotes were loaded
            quote_to_use = random.choice(quotes_from_file)
        elif quotes_from_file and quotes_from_file[0] == "This is a default quote. Create assets/quotes.txt to add your own.":
             quote_to_use = quotes_from_file[0] # Use the default placeholder
        else: # No quotes from file, and no --quote arg
            print("No quotes available from file or arguments. Using a final fallback quote.")
            quote_to_use = "This is a fallback quote. Please provide quotes via --quote or --quote_file."

    if not quote_to_use: # Should not be reached if logic above is correct
        print("Critical Error: No quote selected. Cannot generate video.")
        return

    generate_video(
        quote_text=quote_to_use,
        output_filename=args.output_filename,
        duration_per_quote=args.duration,
        background_path=args.background_path,
        music_path=args.music_path,
        font_path=args.font_path,
        font_size=args.font_size
    )

if __name__ == '__main__':
    main()
