# Video Bookmarks
Tag videos at specific timestamps for easy reference

## Quickstart Pre-Reqs

 - clone the repository locally
 - in the `videobookmarks` directory, 
do`python3 -m pip install .` for setup
 - export a DB_URL environment variable,
use a value with the suffix `_test` to run unit tests
 - export a YouTube API key environment as `YT_API_KEY`. Note that if the API Key has not been shared with you, 
you will need to generate one.

 Use Makefile commands below to run install dependencies and unit tests.

--------------

# Makefile Commands
<i>command line Makefile statements are formatted as: `make <command>` 
```commandline
venv      - set up virtual environment (Optional)
install   - Install dependencies
test      - Run unit tests
clean     - Clean up compiled Python files and __pycache__
help      - Display this help message
```
