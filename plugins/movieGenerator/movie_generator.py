import os
import re
import sys
import json

try:
    import stashapi.log as log
    from stashapi.tools import file_to_base64
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    print(
        "You need to install the stashapi module. (pip install stashapp-tools)",
        file=sys.stderr,
    )


class Movie:
    def __init__(self, name):
        self.name = name
        self.cover = None

    def __repr__(self):
        return f"Movie(name={self.name}, cover={self.cover}"


def is_movie_in_list(movies, movie_name):
    for movie in movies:
        if movie.name.lower() == movie_name.lower():
            return True
    return False


class Gallery:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Gallery(name={self.name}"


def is_gallery_in_list(galleries, gallery_name):
    for gallery in galleries:
        if gallery.name.lower() == gallery_name.lower():
            return True
    return False


# Find paths to iterate on
def get_stash_paths():
    config = stash.get_configuration("general { stashes { path excludeVideo } }")
    stashes = config["general"]["stashes"]
    return [s["path"] for s in stashes if not s["excludeVideo"]]


def main():
    global stash
    json_input = json.loads(sys.stdin.read())

    stash = StashInterface(json_input["server_connection"])

    ROOT_PATH = get_stash_paths()

    movies = []
    galleries = []

    for stash_path in ROOT_PATH:
        # log.info("Stash Path: " + stash_path)

        for root, dirs, files in os.walk(stash_path):
            # log.info("Root: " + root)

            if len(files) == 0:
                # log.info("No files in this folder. Skipping...")
                continue

            # If the movie isn't in the current list of movies add it
            movie_created = False
            if not is_movie_in_list(movies, os.path.basename(root)):
                try:
                    new_movie = create_movie(root, files)
                    get_movie_cover(root, new_movie)
                    movies.append(new_movie)
                    movie_created = True
                except Exception as error:
                    log.warning(error)

            # If a movie was created and gallery already not in list, iterate through all its directories for galleries
            if movie_created and not is_gallery_in_list(
                galleries, os.path.basename(root)
            ):
                try:
                    galleries.append(create_gallery(root))
                except Exception as error:
                    log.warning(error)

    # for movie in movies:
    #     log.info("\n")
    #     log.info(movie)
    #     log.info("\n")

    # for gallery in galleries:
    #     log.info("\n")
    #     log.info(gallery)
    #     log.info("\n")

    stash_create_movies(movies)
    stash_create_galleries(galleries)

    out = json.dumps({"output": "ok"})
    print(out + "\n")


def get_movie_cover(root, movie):
    pattern = r"(?:thumb|poster|cover)\.(?:jpg|png|webp)"
    for local_root, dirs, files in os.walk(root):
        for file in files:
            if re.search(pattern, file):
                movie.cover = os.path.join(local_root, file)
                return


def create_movie(root, files):
    video_extensions = {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".flv",
        ".wmv",
        ".m4v",
        ".mpeg",
        ".mpg",
    }

    # If no video files, don't create a movie
    if not any(os.path.splitext(file)[1].lower() in video_extensions for file in files):
        raise ValueError("No video files found in the directory " + root)

    return Movie(os.path.basename(root))


def create_gallery(root):
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

    new_gallery = Gallery(os.path.basename(root))

    for root, _, files in os.walk(root):
        for file in files:
            if os.path.splitext(file)[1].lower() in image_extensions:
                return new_gallery

    # If didn't return early, throw error
    raise ValueError("No image files found in the directory " + root)

def stash_find_existing_movie(movie):
    existing_movie = stash.find_movie(movie_in={"name": movie.name})

    return existing_movie


def stash_find_existing_gallery(gallery):
    search = {"title": {"modifier": "EQUALS", "value": gallery.name}}
    # log.info("Searching with details: ")
    # log.info(search)
    existing_gallery = stash.find_galleries(f=search)

    # log.info("Existing Gallery: ")
    # log.info(existing_gallery)

    return existing_gallery


def stash_create_movies(movies):
    for movie in movies:
        existing_id = stash_find_existing_movie(movie)

        movie_in = { "name": movie.name }
        if movie.cover is not None:
            movie_in["front_image"] = file_to_base64(movie.cover)

        if existing_id is None:
            new_movie = stash.create_movie(
                movie_in={movie_in}
            )
            # log.info("New Movie: ")
            # log.info(new_movie)
            existing_id = new_movie.get("id")
        else:
            existing_id = existing_id.get("id")

        # log.info("Curent ID: ")
        # log.info(existing_id)

        stash_add_scenes_to_movie(movie, existing_id)

def stash_add_scenes_to_movie(movie, movie_id):
    scenes = stash.find_scenes(
        f={"path": {"modifier": "INCLUDES", "value": f'{movie.name}"'}}
    )

    movie_metadata = {"movie_id": movie_id}

    for scene in scenes:
        # log.info("Current Scene: ")
        # log.info(scene)
        update_scene = True
        for movie_entry in scene.get("movies"):
            if movie_entry.get("movie").get("id") == str(movie_id):
                update_scene = False
                return
        if update_scene:
            stash.update_scene({"id": scene["id"], "movies": [movie_metadata]})
        else:
            log.info("Skipped updating for scene with ID " + scene["id"])

def stash_create_galleries(galleries):
    for gallery in galleries:
        existing_id = stash_find_existing_gallery(gallery)

        if existing_id is None or len(existing_id) == 0:
            new_gallery = stash.create_gallery(
                gallery_create_input={"title": gallery.name}
            )
            # log.info("New Gallery: ")
            existing_id = str(new_gallery)
        else:
            existing_id = existing_id[0].get("id")

        # log.info("Current ID: ")
        log.info(existing_id)

        stash_add_images_to_gallery(gallery, existing_id)

def stash_add_images_to_gallery(gallery, gallery_id):
    search = {"path": {"modifier": "INCLUDES", "value": gallery.name}}
    images = stash.find_images(
        f=search,
    )

    images_to_update = []

    for image in images:
        update_image = True
        for current_image_gallery in image.get("galleries"):
            if current_image_gallery.get("id") == str(gallery_id):
                update_image = False
        if update_image:
            images_to_update.append(image.get("id"))
        else:
            log.info("Skipped updating for gallery with ID " + image["id"])
    
    stash.add_gallery_images(gallery_id, images_to_update)
    log.info(f"Updated gallery and added {len(images_to_update)} images.")


if __name__ == "__main__":
    main()
