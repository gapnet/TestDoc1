# YouTube Video Generator

This tool helps in generating YouTube videos featuring quotes overlaid on dynamic backgrounds with lofi music.

## Features
*   Uses quotes from a text file or a direct command-line argument.
*   Selects random backgrounds from a user-provided image/video folder.
*   Selects random lofi music from a user-provided music folder.
*   Customizable font, font size, and output duration.
*   Generates MP4 video files.

## Setup

1.  **Navigate to the tool's directory**:
    ```bash
    cd video_generator
    ```

2.  **Install Dependencies**:
    Make sure you have Python 3.7+ installed. It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    This will install `moviepy`, `Pillow`, and their dependencies.

3.  **Add Assets**:
    *   **Quotes**: Add your quotes (one per line) to the `assets/quotes.txt` file, or use the `--quote` / `--quote_file` arguments.
    *   **Backgrounds**: Place your background image files (e.g., `.jpg`, `.png`) or short video loop files (e.g., `.mp4`, `.mov`) into the `assets/backgrounds/` directory.
    *   **Music**: Place your lofi music tracks (e.g., `.mp3`, `.wav`) into the `assets/music/` directory.
    The script includes placeholder files in these directories to guide you.

4.  **Font**:
    The script attempts to use "arial.ttf" by default.
    *   Ensure you have a common font like Arial installed on your system if you rely on the default.
    *   Alternatively, you can specify the path to any `.ttf` font file using the `--font_path` argument. You might need to copy a `.ttf` file (e.g., `arial.ttf`) into the `video_generator` directory or provide a full path to it.

## Usage

Run the script from within the `video_generator` directory:

```bash
python generator.py [OPTIONS]
```

**Common Options**:

*   `--quote "Your specific quote here"`: Provide a quote directly.
*   `--quote_file path/to/your/quotes.txt`: Specify a custom quotes file.
*   `--background_path path/to/your/bg.mp4`: Use a specific background.
*   `--music_path path/to/your/music.mp3`: Use a specific music file.
*   `--output_filename my_video.mp4`: Set the output file name.
*   `--duration 15`: Set the duration (in seconds) for the quote display.
*   `--font_path /path/to/your/font.ttf`: Specify a font file.
*   `--font_size 90`: Set the font size.

**Examples**:

1.  **Generate a video with a random quote, background, and music from the `assets` folder**:
    ```bash
    python generator.py
    ```
    (This will create `output.mp4` if assets are available.)

2.  **Generate a video with a specific quote and output name**:
    ```bash
    python generator.py --quote "Stay hungry, stay foolish." --output_filename steve_jobs_quote.mp4
    ```

3.  **Generate a 15-second video using a specific background and font**:
    ```bash
    python generator.py --background_path assets/backgrounds/my_cool_loop.mp4 --font_path /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf --duration 15
    ```

For a full list of options, run:
```bash
python generator.py --help
```
