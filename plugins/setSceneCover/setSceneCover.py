import os
import re
import sys
import json
import time

try:
    import stashapi.log as log
    from stashapi.tools import file_to_base64
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    print(
        "You need to install the stashapi module. (pip install stashapp-tools)",
        file=sys.stderr,
    )

MANUAL_ROOT = None
cover_pattern = r"(?:poster|cover)\.(?:jpg|png|jpeg|webp)"


def main():
    global stash, mode_arg
    json_input = json.loads(sys.stdin.read())

    stash = StashInterface(json_input["server_connection"])
    mode_arg = json_input["args"]["mode"]

    try:
        if MANUAL_ROOT:
            scan(MANUAL_ROOT, handle_cover)
        else:
            for stash_path in get_stash_paths():
                scan(stash_path, handle_cover)
    except Exception as e:
        log.error(e)

    out = json.dumps({"output": "ok"})
    print(out + "\n")


def handle_cover(path, file):
    filepath = os.path.join(path, file)

    b64img = file_to_base64(filepath)
    if not b64img:
        log.warning(f"Could not parse {filepath} to b64image")
        return

    scenes = stash.find_scenes(
        f={"path": {"modifier": "INCLUDES", "value": f'{path}"'}}, fragment="id"
    )

    log.info(f'Found Cover: {[int(s["id"]) for s in scenes]}|{filepath}')

    for scene in scenes:
        if mode_arg == "set_cover":
            update_scene(scene, b64img)
        else:
            log.info(f"Applied cover to scene {scene['id']}")

def update_scene(scene, b64img):
    retry_count = 0
    while retry_count < 5:
        try:
            stash.update_scene({"id": scene["id"], "cover_image": b64img})
            log.info(f"Applied cover to scene {scene['id']}")
            break

        except Exception as e:
            if "database is temporarily locked" in str(e):
                log.warning(f"Database locked, retrying... {retry_count + 1}")
                time.sleep(1)
                retry_count += 1
            else:
                log.error(f"Failed to update scene {scene['id']}: {e}")
                break
    else:
        log.error(f"Failed to update scene {scene['id']} after 5 retries")

def get_stash_paths():
    config = stash.get_configuration("general { stashes { path excludeVideo } }")
    stashes = config["general"]["stashes"]
    return [s["path"] for s in stashes if not s["excludeVideo"]]


def scan(ROOT_PATH, _callback):
    log.info(f"Scanning {ROOT_PATH}")
    current_time = time.time()
    three_days_ago = current_time - 3 * 24 * 60 * 60
    
    log.info(f"Using mode '{mode_arg}'...")
    
    for root, dirs, files in os.walk(ROOT_PATH):
        for file in files:
            if re.match(cover_pattern, file, re.IGNORECASE):
                if mode_arg != "set_cover_recent":
                    _callback(root, file)
                else:
                    filepath = os.path.join(root, file)
                    file_mtime = os.path.getmtime(filepath)
                    if file_mtime >= three_days_ago:
                        log.info(f"File {file} is les than 3 days ago. Updating...")
                        _callback(root, file)

if __name__ == "__main__":
    main()
