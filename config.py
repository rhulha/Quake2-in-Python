"""
config.py - Game configuration management
Loads and manages game settings from config files
"""

import os
import json

CONFIG_FILE = "quake2_config.json"


def load_config():
    """Load configuration from file"""
    config = {
        "quake2_dir": None,
        "width": 800,
        "height": 600,
        "fullscreen": False,
        "debug": False,
    }

    # Try to load config file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                config.update(loaded)
                print(f"Loaded config from {CONFIG_FILE}")
        except Exception as e:
            print(f"Failed to load {CONFIG_FILE}: {e}")

    return config


def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            print(f"Saved config to {CONFIG_FILE}")
    except Exception as e:
        print(f"Failed to save {CONFIG_FILE}: {e}")


def set_quake2_directory(directory):
    """Set and save the Quake 2 directory"""
    config = load_config()
    config["quake2_dir"] = directory
    save_config(config)
    print(f"Set Quake 2 directory to: {directory}")


def get_quake2_directory(config=None):
    """Get the Quake 2 directory from config"""
    if config is None:
        config = load_config()

    quake2_dir = config.get("quake2_dir")

    if quake2_dir and os.path.isdir(quake2_dir):
        return quake2_dir

    # Return None to use default search paths
    return None


def create_default_config():
    """Create a default config file with instructions"""
    default_config = {
        "quake2_dir": "D:\\SteamLibrary\\steamapps\\common\\Quake 2\\baseq2",
        "width": 800,
        "height": 600,
        "fullscreen": False,
        "debug": False,
    }

    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        print(f"Created default config file: {CONFIG_FILE}")
        print("Please edit this file and set quake2_dir to your Quake 2 installation path.")
