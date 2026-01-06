#!/usr/bin/env python3

import os
import subprocess
import sys

def main():
    # Set environment variables for libcamera
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = '/usr/local/lib/aarch64-linux-gnu:' + env.get('LD_LIBRARY_PATH', '')
    env['GST_PLUGIN_PATH'] = '/usr/local/lib/aarch64-linux-gnu/gstreamer-1.0:' + env.get('GST_PLUGIN_PATH', '')

    # Use our gstreamer camera node directly with proper environment
    print("Starting GStreamer camera node with libcamera support...")
    gstreamer_cmd = [sys.executable, os.path.join(os.path.dirname(__file__), 'gstreamer_camera_node.py')]

    try:
        subprocess.run(gstreamer_cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"GStreamer camera node failed: {e}")
        sys.exit(e.returncode)
    except FileNotFoundError as e:
        print(f"GStreamer camera node not found: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
