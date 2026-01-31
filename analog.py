import os
import gzip
import json
import logging

logger = logging.getLogger(__name__)

langs = {}

for file in os.listdir('locale'):
    if file.endswith('.json'):
        lang_code = file[:-5]
        with open(os.path.join('locale', file), 'r', encoding='utf-8') as f:
            try:
                langs[lang_code] = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {file}: {e}")

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

def process_basic_file(lines,lang_code):
    content = "```\n"
    for line in lines:
        if line.startswith("Kernel:"):
            content += langs[lang_code]["kernel_version"].format(version=line.split(': ', 1)[1]) + "\n"
        elif line.startswith("FINGERPRINT:"):
            content += langs[lang_code]["fingerprint"].format(fingerprint=line.split(': ', 1)[1]) + "\n"
        elif line.startswith("MODEL:"):
            content += langs[lang_code]["device_model"].format(model=line.split(': ', 1)[1]) + "\n"
        elif line.startswith("PRODUCT:"):
            content += langs[lang_code]["device_codename"].format(codename=line.split(': ', 1)[1]) + "\n"
        elif line.startswith("Machine:"):
            content += langs[lang_code]["device_arch"].format(arch=line.split(': ', 1)[1]) + "\n"
        elif line.startswith("SafeMode:"):
            content += langs[lang_code]["ksu_safe_mode"].format(safemode=line.split(': ', 1)[1]) + "\n"
        elif line.startswith("KernelSU:"):
            content += langs[lang_code]["ksu_version"].format(version=line.split(': ', 1)[1]) + "\n"
        elif line.startswith("LKM:"):
            content += langs[lang_code]["ksu_lkm_mode"].format(status=line.split(': ', 1)[1]) + "\n"
    return content + "```\n"

def process_defconfig_file(lines,lang_code):
    pass

def process_module_json(datas,lang_code):
    content = "```\n"
    for data in datas:
        if data.get('enabled') == 'true':
            content += "" +  langs[lang_code]["module_details"].format(name=data.get('name'), version=data.get('version'), id=data.get('id')) + "\n"
    return content + "```\n"

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