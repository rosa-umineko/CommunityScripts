from scanner import get_image_url

import os
import sys
import json

try:
    import stashapi.log as log
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    print(
        "You need to install the stashapi module. (pip install stashapp-tools)",
        file=sys.stderr,
    )
    sys.exit(1)

def main():
    global stash, mode_arg
    json_input = json.loads(sys.stdin.read())

    stash = StashInterface(json_input["server_connection"])
    mode_arg = json_input["args"]["mode"]

    try:
        add_images_to_tags()
    except Exception as e:
        log.error(e)

    out = json.dumps({"output": "ok"})
    print(out + "\n")

def add_images_to_tags():
    log.info("Not implemented.")
  
    pass

if __name__ == "__main__":
    main()
