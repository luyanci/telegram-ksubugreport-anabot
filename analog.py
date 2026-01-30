import os
import gzip
import json
from loguru import logger

def unpack_tar_gz(file_path, output_path):
    """Unpacks a .tar.gz file to the specified output path."""
    import tarfile

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with tarfile.open(file_path, 'r:gz') as tar:
            for file in tar.getmembers():
                try:
                    tar.extract(file, output_path)
                except Exception as e:
                    logger.warning(f"Error extracting {file.name}: {e}")
                    continue

def read_basic_txt(file_path):
    """Reads a BASIC .txt file and returns its content as a list of lines."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    return [line.strip() for line in lines]

def read_defconfig_gz(file_path):
    """Reads a compressed .defconfig.gz file and returns its content as a list of lines."""
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with gzip.open(file_path, 'rt') as file:
        lines = file.readlines()
    
    return [line.strip() for line in lines] 

def read_module_json(file_path):
    """Reads a module.json file and returns its content as a dictionary."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    return data

if __name__ == "__main__":
    # Example usage
    basic_file_path = 'test1/basic.txt'
    defconfig_file_path = 'test1/defconfig.gz'
    
    try:
        basic_lines = read_basic_txt(basic_file_path)
        print("BASIC .txt file content:")
        for line in basic_lines:
            logger.info(line.split(': ')[1])  # Log only the value part
    except FileNotFoundError as e:
        print(e)
    
    try:
        defconfig_lines = read_defconfig_gz(defconfig_file_path)
        print("\n.defconfig.gz file content:")

    except FileNotFoundError as e:
        print(e)
        
    try:
        module_json_path = 'test1/modules.json'
        module_data = read_module_json(module_json_path)
        print("\nModule .json file content:")
        logger.info(module_data)

    except FileNotFoundError as e:
        print(e)