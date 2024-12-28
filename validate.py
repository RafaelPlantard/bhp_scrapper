# Iterate over commentary folder and check if any key-value is blank or missing

import os
import json
import sys

for root, dirs, files in os.walk('commentary'):
    for file in files:
        with open(os.path.join(root, file), 'r') as f:
            data = f.read()
            if not data:
                print(f'File {file} is empty')
                sys.exit(1)
            try:
                json_data = json.loads(data)
                if not json_data:
                    print(f'File {file} is empty')
                    sys.exit(1)
            except json.JSONDecodeError:
                print(f'File {file} is not valid JSON')
                sys.exit(1)

            for key in json_data:
                if not json_data[key]:
                    print(f'Key {key} in file {file} is empty')
                    sys.exit(1)

print('All files are valid')
