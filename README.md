# frogger-agent

## Software/Hardware Requirments

- macOS (tested on Mac Tahoe) or Linux
- Tested on Python 3.14.2
- Homebrew (for MacOS 10 or higher) https://brew.sh

### Installation Process for MacOS 10 or higher
1. Run `brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf pkg-config`
2. Create and activate virtual environment:
    - `python -m venv .venv` 
    - `source venv/bin/activate`
3. Run `pip install pygame`

To verify installation, you can run `python -m pygame.examples.aliens`, if the game shows up and you can play it, then installation was done properly.

For more details on pygame installation, you can go to https://www.pygame.org/wiki/MacCompile. For more general details on pygame installion, you can go to https://www.pygame.org/wiki/GettingStarted.

## Running Frogger
Run `python frogger.py`