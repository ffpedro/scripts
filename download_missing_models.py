# Usage
#     python3 download_missing_models.py -f <project_map_file.yaml>
#     python3 download_missing_models.py -f <project_map_file.yaml> -p <path_to_models>
#
# Description
#     This script will download all missing models
#     (from Fuel server) for a given map file.
#     Default models path: '$HOME/.gazebo/models/'
#

import getopt
import os
import requests
import sys
import yaml
import zipfile
from pathlib import Path

def download_with_resume(sess: requests.Session, url: str) -> bytes:
    data = b""
    expected_length = None
    for attempt in range(50):
        if len(data) == expected_length:
            break
        if len(data):
            headers = {"Range": f"bytes={len(data)}-"}
            expected_status = 206
        else:
            headers = {}
            expected_status = 200
        print(f"{url}: got {len(data)} / {expected_length} bytes...")
        resp = sess.get(url, stream=True, headers=headers)
        resp.raise_for_status()
        if resp.status_code != expected_status:
            raise ValueError(f"Unexpected status code: {resp.status_code}")
        if expected_length is None:  # Only update this on the first request
            content_length = resp.headers.get("Content-Length")
            if not content_length:
                raise ValueError("Content-Length header not found")
            expected_length = int(content_length)

        try:
            for chunk in resp.iter_content(chunk_size=8192):
                data += chunk
        except requests.exceptions.ChunkedEncodingError:
            pass

    if len(data) != expected_length:
        raise ValueError(f"Expected {expected_length} bytes, got {len(data)}")

    return data

# Parse yaml file to get models list
def parse_map_file(input_filename):
        models = {}
        if not os.path.isfile(input_filename):
            raise FileNotFoundError(f'input file {input_filename} not found')

        with open(input_filename, 'r') as f:
            yaml_node = yaml.load(f, Loader=yaml.CLoader)

            for level_name, level_yaml in yaml_node['levels'].items():
                print('Getting models from level: {}'.format(level_name))
                for model in level_yaml['models']:
                    field_name = model['model_name']
                    if '/' not in field_name:
                        print('Model "{}" without author, ignoring it.'.format(field_name))
                        continue
                    author, model_name = field_name.split('/')
                    if author not in models:
                        models[author] = set()
                    models[author].add(model_name)

        return models

map_file = None

# Default Models Path
home_path = Path.home()
models_path = home_path.joinpath('.gazebo/models/')

# Read options
optlist, args = getopt.getopt(sys.argv[1:], 'f:')

for option, value in optlist:
    if option == "-f":
        map_file = value
    if option == "-p":
        models_path = Path(value)

if not map_file:
    print('Error: missing `-f <project_map_file.yaml>` option')
    quit()


print('Downloading models for the following map file: {}'.format(map_file))

# Get models data
models = parse_map_file(map_file)

# The Fuel server URL.
base_url ='https://fuel.gazebosim.org/'

# Fuel server version.
fuel_version = '1.0'

for author, model_names in models.items():
    for model_name in model_names:

        export_path = models_path.joinpath(model_name)

        # Check if model already exists
        if export_path.exists() or export_path.is_dir():
            print('Model {} already exists, skipping...'.format(model_name))
            continue

        print('Downloading {} by {} from Fuel'.format(model_name, author))

        # Path to download a single model in the collection
        file_name = model_name + '.zip'
        download_url = base_url + fuel_version + '/{}/models/{}'.format(author, file_name)

        with requests.Session() as sess:
            data = download_with_resume(
                sess,
                url=download_url,
            )

        with open(file_name, 'wb') as fd:
            fd.write(data)

        # Extract content and export them to models path
        print('Extracting {} data to {}'.format(model_name, export_path))
        export_path.mkdir()
        with zipfile.ZipFile(file_name) as zf:
            zf.extractall(export_path)

        os.remove(file_name)

print('Done.')
