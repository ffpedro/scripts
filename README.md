# Scripts
Useful scripts for robotics.

## download_missing_models.py - Download missing models for Gazebo
This script will download all missing models (from Fuel server) for a given map file.
Default models path: '$HOME/.gazebo/models/'

Run it with the default path to models:
```shell
python3 download_missing_models.py -f <project_map_file.yaml>
```

Specify a different path to models:
```shell
python3 download_missing_models.py -f <project_map_file.yaml> -p <path_to_models>
``` 
