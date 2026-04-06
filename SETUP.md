# Quake 2 Python - Setup Instructions

## Loading Game Resources

This game requires Quake 2 game resources (maps, models, textures, sprites, sounds) to run. These files are not included with this project due to copyright restrictions.

### Option 1: Using Steam Quake 2 (Recommended)

The easiest way is to use your existing Steam Quake 2 installation:

1. **Install Quake 2 from Steam** (if you haven't already):
   - Open Steam
   - Search for "Quake 2"
   - Click Install

2. **Configure the game path**:
   - When you first run the game, a `quake2_config.json` file will be created
   - Edit `quake2_config.json` and set the `quake2_dir` to your Steam installation:

   ```json
   {
     "quake2_dir": "D:\\SteamLibrary\\steamapps\\common\\Quake 2\\baseq2",
     "width": 800,
     "height": 600,
     "fullscreen": false,
     "debug": false
   }
   ```

3. **Common Steam installation paths**:
   - Default: `D:\SteamLibrary\steamapps\common\Quake 2\baseq2`
   - Alternative: `C:\Program Files\Steam\steamapps\common\Quake 2\baseq2`
   - Alternative: `C:\Program Files (x86)\Steam\steamapps\common\Quake 2\baseq2`

### Option 2: Manual Setup

If you have the original Quake 2 CD or files:

1. Copy the entire `baseq2` folder to your Quake 2 Python directory, OR
2. Copy all `.pak` files from your Quake 2 installation to a `baseq2` folder in the project directory

Required PAK files:
- `pak0.pak` - Core game resources (maps, sprites, sounds)
- `pak1.pak` - Game executable and additional resources
- `pak2.pak` - Game media and textures

### Verifying Your Setup

The game will print a message on startup indicating where it found the resources:

```
Found Quake 2 resources at: D:\SteamLibrary\steamapps\common\Quake 2\baseq2
```

If you see a warning message instead, the resources were not found. Check your `quake2_config.json` file.

## Configuration File (quake2_config.json)

This file is auto-created on first run with default values:

```json
{
  "quake2_dir": "D:\\SteamLibrary\\steamapps\\common\\Quake 2\\baseq2",
  "width": 800,
  "height": 600,
  "fullscreen": false,
  "debug": false
}
```

**Configuration Options:**
- `quake2_dir`: Path to the Quake 2 baseq2 directory (required)
- `width`: Screen width in pixels (default: 800)
- `height`: Screen height in pixels (default: 600)
- `fullscreen`: Run in fullscreen mode (true/false)
- `debug`: Enable debug output (true/false)

## Troubleshooting

### "Could not find Quake 2 resources directory"

This means the game couldn't find your Quake 2 installation. Solutions:

1. **Check quake2_config.json**:
   - Make sure the path exists and is correctly formatted
   - Use `\\` for backslashes in JSON: `D:\\SteamLibrary\\steamapps\\...`

2. **Verify the directory**:
   - Open File Explorer and navigate to the path
   - Confirm that `pak0.pak`, `pak1.pak`, etc. exist there

3. **Update the path**:
   - Edit `quake2_config.json` with the correct Steam installation path
   - Save and restart the game

### "Missing PAK files"

If the game crashes or reports missing files:

1. Verify that `pak0.pak` and `pak1.pak` exist in your baseq2 directory
2. These files are part of your Steam Quake 2 installation
3. If they're missing, reinstall Quake 2 from Steam

## Running the Game

Once setup is complete:

```bash
python main.py
```

Or on Windows:

```bash
python main.py +map base1
```

This will start the game and automatically load the first map (`base1`).

## Getting Help

If you have issues:

1. Check the console output for error messages
2. Verify your `quake2_config.json` file exists and has a valid path
3. Make sure Quake 2 is installed from Steam
4. Check that the baseq2 directory contains the required PAK files

Enjoy Quake 2!
