import os
import gzip
import json
import logging
from locates import langs

MAX_FILE_SIZE= 50*1024*1024  # 50 MB

logger = logging.getLogger(__name__)


def unpack_tar_gz(file_path, output_path):
    """Unpacks a .tar.gz file to the specified output path."""
    import tarfile

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with tarfile.open(file_path, 'r:gz') as tar:
            for file in tar.getmembers():
                if file.size > MAX_FILE_SIZE:
                    logger.warning(f"Skipping extraction of {file.name} due to size > {MAX_FILE_SIZE} bytes.")
                    continue
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
        logger.warning(f"The file {file_path} does not exist.")
        return []
    
    if file_path.endswith('.gz'):
        with gzip.open(file_path, 'rt') as file:
            lines = file.readlines()
    else:
        with open(file_path, 'r') as file:
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
    def parse_line_value(line):
        parts = line.split(': ', 1)
        return parts[1] if len(parts) >= 2 else ""
    
    content = "<blockquote expandable>"
    for line in lines:
        if line.startswith("Kernel:"):
            content += langs[lang_code]["kernel_version"].format(version=parse_line_value(line)) + "\n"
        elif line.startswith("FINGERPRINT:"):
            content += langs[lang_code]["fingerprint"].format(fingerprint=parse_line_value(line)) + "\n"
        elif line.startswith("MODEL:"):
            content += langs[lang_code]["device_model"].format(model=parse_line_value(line)) + "\n"
        elif line.startswith("PRODUCT:"):
            content += langs[lang_code]["device_codename"].format(codename=parse_line_value(line)) + "\n"
        elif line.startswith("Machine:"):
            content += langs[lang_code]["device_arch"].format(arch=parse_line_value(line)) + "\n"
        elif line.startswith("SELinux:"):
            content += langs[lang_code]["selinux_status"].format(status=parse_line_value(line)) + "\n"
        elif line.startswith("Manager:"):
            content += langs[lang_code]["manager_version"].format(manager=parse_line_value(line)) + "\n"
        elif line.startswith("KernelSU:"):
            content += langs[lang_code]["ksu_version"].format(version=parse_line_value(line)) + "\n"
        elif line.startswith("LKM:"):
            content += langs[lang_code]["ksu_lkm_mode"].format(status=parse_line_value(line)) + "\n"
        elif line.startswith("APatch:"):
            content += langs[lang_code]["apatch_version"].format(version=parse_line_value(line)) + "\n"
        elif line.startswith("KPatch:"):
            content += langs[lang_code]["kpatch_version"].format(version=parse_line_value(line)) + "\n"
        elif line.startswith("SafeMode:"):
            content += langs[lang_code]["safe_mode"].format(safemode=parse_line_value(line)) + "\n"
        
    return content + "</blockquote>\n"

def process_defconfig_file(lines,lang_code):
    response = "<blockquote expandable>"
    blank = True
    for line in lines:
        if line.split('=')[0].find('CONFIG_KSU') != -1:
            blank = False
            response += line + "\n"
        elif line.split('=')[0].find('CONFIG_BBG') != -1:
            blank = False
            response += line + "\n"
        elif line.split('=')[0].find('CONFIG_OVERLAY') != -1:
            blank = False
            response += line + "\n"
        elif line.split('=')[0].find('CONFIG_TMPFS') != -1:
            blank = False
            response += line + "\n"
    if blank:
        response += f"{langs[lang_code]['no_ksu_bbg_config']}\n"
    return response + "</blockquote>\n"

def process_module_json(datas,lang_code):
    content = "<blockquote expandable>"
    if len(datas) != 0:
        for data in datas:
            if data.get('enabled') == 'true':
                content += "✅" + " " +  langs[lang_code]["module_details"].format(name=data.get('name'), version=data.get('version'), id=data.get('id')) + "\n"
            else:
                content += "❌" + " " +  langs[lang_code]["module_details"].format(name=data.get('name'), version=data.get('version'), id=data.get('id')) + "\n"
    else:
        content += f"{langs[lang_code]['no_modules_found']}\n"
    return content + "</blockquote>\n"

def process_file(file_path: str, lang_code: str,timestamp) -> str:
    response = ""
    try:
        unpack_tar_gz(file_path, f'extracted_files_{timestamp}')
        basic_lines = read_basic_txt(f'extracted_files_{timestamp}/basic.txt')
        if os.path.exists(f'extracted_files_{timestamp}/defconfig.gz'):
            defconfig_lines = read_defconfig_gz(f'extracted_files_{timestamp}/defconfig.gz')
        elif os.path.exists(f'extracted_files_{timestamp}/defconfig'):
            defconfig_lines = read_basic_txt(f'extracted_files_{timestamp}/defconfig')
        module_data = read_module_json(f'extracted_files_{timestamp}/modules.json')
        response += "basic.txt:\n"
        response += process_basic_file(basic_lines, lang_code)
        response += "defconfig:\n"
        response += process_defconfig_file(defconfig_lines, lang_code)
        response += f"{langs[lang_code]['modules_info']}\n"
        response += process_module_json(module_data, lang_code)
    except FileNotFoundError as e:
        logger.info(f"Error processing file: {e}")
    return response

def process_need_send_file(timestamp: int) -> dict[list[str], list[str], list[str], list[str]]:
    need_files = ["modules.json","ap_tree.txt","adb_tree.txt","adb_details.txt","pstore.tar.gz","dmesg.txt","oplus.tar.gz","bootlog.tar.gz"]
    can_send_files = []
    missing_files = []
    broken_files = []
    too_large_files = []
    AP_COMPAT= False
    
    # APatch compatibility check,if one of the two files is missing,remove it from need_files
    if not os.path.exists(f'extracted_files_{timestamp}/ap_tree.txt'):
        need_files.remove("ap_tree.txt")
    elif not os.path.exists(f'extracted_files_{timestamp}/adb_tree.txt'):
        AP_COMPAT = True
        need_files.remove("adb_tree.txt")
    
    for file in need_files:
        if not os.path.exists(f'extracted_files_{timestamp}/{file}'):
            if AP_COMPAT and file in ["adb_details.txt","oplus.tar.gz"]:
                continue
            missing_files.append(file)
            continue
        elif os.path.getsize(f'extracted_files_{timestamp}/{file}') < 1000:
            broken_files.append(file)
            continue
        elif os.path.getsize(f'extracted_files_{timestamp}/{file}') > MAX_FILE_SIZE:
            too_large_files.append(file)
            continue
        else:
            can_send_files.append(file)
            continue
    return can_send_files, missing_files, broken_files, too_large_files

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
