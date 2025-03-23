from scanner import get_image_url
import time
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
    tag_data = stash.find_tags()

    # Loop over each tag and update its image URL if the current image is the default.
    for tag in tag_data:
        # Check if the tag's current image does NOT contain "default=true"
        # (i.e. a custom image is already set) and skip if so.
        current_image = tag.get("image_path")
        if "default=true" not in current_image:
            log.info(f"Tag '{tag['name']}' (ID: {tag['id']}) already has a custom image. Skipping update.")
            continue

        try:
            # Build the search query by combining the tag's name with "porn"
            query = f"{tag['name']} porn"
            # Retrieve a new image URL based on the search query.
            # If get_image_url returns an object with a .src attribute, adjust accordingly.
            image_result = get_image_url(query)
            
            # If the result is an object with a src attribute:
            try:
                image_url = image_result.src
            except AttributeError:
                # Otherwise, assume it is a URL string or dictionary
                image_url = image_result if isinstance(image_result, str) else image_result.get("src", image_result.get("image"))

            if not image_url:
                log.error(f"No image URL found for tag '{tag['name']}' (ID: {tag['id']}).")
                continue

            # Prepare the update payload (using the "image" field per API documentation)
            tag_update = {
                "id": tag["id"],
                "image": image_url
            }
            response = stash.update_tag(tag_update)
            log.info(f"Updated tag '{tag['name']}' (ID: {tag['id']}) with new image URL: {image_url}")
        except Exception as e:
            log.error(f"Error updating tag '{tag['name']}' (ID: {tag['id']}): {e}")


  
    pass

if __name__ == "__main__":
    main()