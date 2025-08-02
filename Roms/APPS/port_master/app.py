from pathlib import Path
from typing import List, Optional
from main import hw_info, system_lang
from graphic import screen_resolutions
from language import Translator
import graphic as gr
import input
import sys
import time
import socket
from PIL import Image
import os
import re
import json
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
import stat
import logging
import glob

program = os.path.dirname(os.path.abspath(__file__))

GITHUB_API_URL = "https://api.github.com/repos/PortsMaster/PortMaster-GUI/releases/latest"
GITHUB_DOWNLOAD_URL = "https://github.com/PortsMaster/PortMaster-GUI/releases/latest/download/PortMaster.zip"
RUNTIMES_API_URL = "https://api.github.com/repos/kai4man/Anbernic-H700-RG-xx-StockOS-Modification-PM-runtimes/releases/latest"

LEGACY_PORTMASTER_DIR = "/roms/ports/PortMaster"

TEMP_FILE = "/tmp/PortMaster.zip"
TEMP_DIR = "/tmp/PortMaster_Update"
PYLIBS_DIR = os.path.join(LEGACY_PORTMASTER_DIR, "pylibs/harbourmaster")
CONFIG_FILE = os.path.join(PYLIBS_DIR, "config.py")
HARBOUR_FILE = os.path.join(PYLIBS_DIR, "harbour.py")
PUGSCENE_FILE = os.path.join(LEGACY_PORTMASTER_DIR, "pylibs/pugscene.py")

translator = Translator(system_lang)
selected_position = 0
roms_selected_position = 0
selected_system = ""
skip_input_check = False
fix_flg_k4m="make by KAI4MAN"
fix_flg_grh="make by G.R.H"
port_master_github_version = f"#{fix_flg_k4m}"

log_dir = os.path.join(program, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "portmaster.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 11))

button_x = x_size - 130
button_y = y_size - 30
ratio = y_size / x_size

def start() -> None:

    if not is_connected():
        exit_program(f"{translator.translate('No internet connection')}", 3)

    if not check_port_master_version():
        if load_screen_show_update_prompt():
            load_screen_update_port_master()

    if not check_runtimes_version():
        load_creen_runtimes()

    if not check_and_update_pugscene():   
        logger.warning("Предупреждение: проблемы с конфигурацией pugscene.py")

    if not check_and_update_config():
        logger.warning("Предупреждение: проблемы с конфигурацией")
    
    if not check_and_update_harbour():
        logger.warning("Предупреждение: проблемы с конфигурацией harbour.py")
    
    if not other_update():
        logger.error("Другие ошибки обновления")

    if not set_portmaster_language():
        logger.error("Ошибка установки языка портмастера")

    clean_exit(*sys.argv[1:])

def is_connected():
    test_servers = [
        ("8.8.8.8", 53),  # google
        ("1.1.1.1", 53),       # NTP DNS
        ("223.5.5.5", 53),       # ali DNS
        ("220.181.38.148", 80)   # baidu
    ]
    for host, port in test_servers:
        try:
            sock = socket.create_connection((host, port), timeout=3)
            sock.close()
            return True
        except (socket.timeout, socket.error):
            continue
    return False
    
def exit_program(error_message: str = "", time_sleep: int = 0) -> None:
    if error_message:
        gr.draw_log(
            error_message, fill=gr.colorBlue, outline=gr.colorBlueD1
        )

    gr.draw_paint()
    time.sleep(time_sleep)
    sys.exit(1)

def check_and_update_pugscene():
    if not os.path.exists(PUGSCENE_FILE):
        logger.warning(f"Файл {PUGSCENE_FILE} не существует")
        return True

    try:
        with open(PUGSCENE_FILE, 'r') as f:
            content = f.read()
        
        if f'#{fix_flg_k4m}' in content:
            return True
            
        lines = content.splitlines()
        lines.insert(0, f'#{fix_flg_k4m}')
        
        stockos_block = '''
        elif Path("/roms/ports").is_dir():
            if '/mnt/sdcard' in subprocess.getoutput(['df']):
                SYSTEM_SD_TOGGLE = Path('/roms/ports/PortMaster/config/system_sd_toggle.txt')

                self.tags['option_list'].add_option(
                    'system-port-mode-toggle',
                    _("Ports Location: ") +  (SYSTEM_SD_TOGGLE.is_file() and _("SD 1") or _("SD 2")),
                    description=_("Location where ports should be installed to."))
'''
        search_string = "self.tags['option_list'].add_option(None, _(\"System\"))"
        found = False
        for line in lines:
            if search_string in line:
                lines.insert(lines.index(line), stockos_block)
                found = True
                break
        
        if not found:
            return False

        toggle_block = '''
            if selected_option == 'system-port-mode-toggle':
                if '/mnt/sdcard' in subprocess.getoutput(['df']):
                    MUOS_MMC_TOGGLE = Path('/roms/ports/PortMaster/config/system_sd_toggle.txt')

                    language_map = {
                        True:  _('SDCARD 1'),
                        False: _('SDCARD 2'),
                    }

                    if self.gui.message_box(
                            _("Are you sure you want to manage and install ports on {to_loc}?\\n\\nAlready installed ports will not be moved.\\nPortMaster will restart for this to take effect.").format(
                                to_loc=language_map[(not MUOS_MMC_TOGGLE.is_file())]),
                            want_cancel=True):

                        self.gui.events.running = False

                        if MUOS_MMC_TOGGLE.is_file():
                            MUOS_MMC_TOGGLE.unlink()
                        else:
                            MUOS_MMC_TOGGLE.touch(0o644)

                        if not harbourmaster.HM_TESTING:
                            reboot_file = (harbourmaster.HM_TOOLS_DIR / "PortMaster" / ".pugwash-reboot")
                            if not reboot_file.is_file():
                                reboot_file.touch(0o644)

                        return True
'''
        search_string = "if selected_option == 'runtime-manager':"
        found = False
        for line in lines:
            if search_string in line:
                lines.insert(lines.index(line), toggle_block)
                found = True
                break
        
        if not found:
            return False

        os.remove(PUGSCENE_FILE)
            
        with open(PUGSCENE_FILE, "w") as f:
            f.write("\n".join(lines))
            
        return True
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении pugscene.py: {e}")
        return False

def check_and_update_config():
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"Файл {CONFIG_FILE} не существует")
        return True

    try:
        with open(CONFIG_FILE, "r") as f:
            content = f.read()
        
        if f'#{fix_flg_k4m}' in content:
            return True
            
        lines = content.splitlines()
        lines.insert(0, f'#{fix_flg_k4m}')
        
        stockos_block = '''
elif Path("/roms/ports/PortMaster/").is_dir():
    ## stockOS
    HM_DEFAULT_TOOLS_DIR   = Path("/roms/ports")
    HM_DEFAULT_PORTS_DIR   = Path("/mnt/mmc/roms/ports")
    HM_DEFAULT_SCRIPTS_DIR = Path("/mnt/mmc/roms/ports")

    SYSTEM_SD_TOGGLE = Path('/roms/ports/PortMaster/config/system_sd_toggle.txt')

    if not SYSTEM_SD_TOGGLE.is_file() and '/mnt/sdcard' in subprocess.getoutput(['df']):
        HM_DEFAULT_PORTS_DIR   = Path("/mnt/sdcard/roms/ports")
        HM_DEFAULT_SCRIPTS_DIR = Path("/mnt/sdcard/roms/ports")
'''
        search_string = 'elif Path("/opt/system/Tools").is_dir():'
        found = False
        for line in lines:
            if search_string in line:
                lines.insert(lines.index(line), stockos_block)
                found = True
                break
        
        if not found:
            return False
            
        with open(CONFIG_FILE, "w") as f:
            f.write("\n".join(lines))
        return True
            
    except Exception as e:
        logger.error(f"Ошибка обновления конфигурации: {str(e)}")
        return False
    
def check_and_update_harbour():
    if not os.path.exists(HARBOUR_FILE):
        return True

    try:
        with open(HARBOUR_FILE, "r") as f:
            content = f.read()
        
        changes_made = False
        lines = content.splitlines()
        
        if f'#{fix_flg_grh}' not in content:
            lines.insert(0, f'#{fix_flg_grh}')
            changes_made = True
            
            if 'self.install_image(port_info)' not in content:
                for i, line in enumerate(lines):
                    if 'self.callback.message_box(_("Port {download_name!r} installed successfully.").format(download_name=port_nice_name))' in line:
                        lines.insert(i + 2, '        self.install_image(port_info)')
                        changes_made = True
                        break
            
            if 'self.uninstall_image(port_info)' not in content:
                for i, line in enumerate(lines):
                    if 'self.callback.message_box(_("Successfully uninstalled {port_name}").format(port_name=port_info_name))' in line:
                        lines.insert(i + 1, '        self.uninstall_image(port_info)')
                        changes_made = True
                        break
            
            if 'def install_image(self, port_info_list):' not in content:
                install_image_code = '''
    def install_image(self, port_info_list):
        logger.info(f"install_image-->port_info_list: {port_info_list}")
        port_dir = f"{self.ports_dir}"
        port_image_dir = self.ports_dir / "Imgs"
        port_script_filename = None
        for item in port_info_list["items"]:
            if self._ports_dir_exists(item):
                if item.casefold().endswith("/"):
                    part = item.rsplit("/")
                    port_dir = Path(port_dir) / part[0]
                if item.casefold().endswith(".sh"):
                    port_script_filename = os.path.splitext(item)
        port_image_list = port_info_list.get("attr", {}).get("image")
        if isinstance(port_image_list, dict):
            for key, port_image in port_image_list.items():
                if port_image.lower().endswith(".png") or port_image.lower().endswith(".jpg"):
                    port_image_filename = os.path.splitext(port_image)
                    break
                else:
                    return 1
        elif isinstance(port_image_list, str):
            port_image = port_image_list
            port_image_filename = os.path.splitext(port_image)
        if not port_image_dir.exists():
            os.makedirs(port_image_dir, exist_ok=True)
        source_image_path = Path(port_dir) / port_image
        target_image_path = Path(port_image_dir) / f"{port_script_filename[0]}{port_image_filename[1]}"
        logger.info(f"source_image_path: {source_image_path}, target_image_path: {target_image_path}")
        shutil.copy2(source_image_path, target_image_path)
'''
                for i, line in enumerate(lines):
                    if '__all__ = (' in line:
                        lines.insert(i - 1, install_image_code)
                        changes_made = True
                        break
            
            if 'def uninstall_image(self, port_info):' not in content:
                uninstall_image_code = '''
    def uninstall_image(self, port_info):
        logger.info(f"uninstall_image-->port_info: {port_info}")
        port_image_dir = self.ports_dir / "Imgs"
        for item in port_info["items"]:
            if item.casefold().endswith(".sh"):
                port_script_filename = os.path.splitext(item)
        port_image_list = port_info.get("attr", {}).get("image")
        if isinstance(port_image_list, dict):
            for key, port_image in port_image_list.items():
                if port_image.lower().endswith(".png") or port_image.lower().endswith(".jpg"):
                    port_image_filename = os.path.splitext(port_image)
                    break
                else:
                    return 1
        elif isinstance(port_image_list, str):
            port_image = port_image_list
            port_image_filename = os.path.splitext(port_image)
        target_image_path = Path(port_image_dir) / f"{port_script_filename[0]}{port_image_filename[1]}"
        logger.info(f"target_image_path: {target_image_path}")
        if target_image_path.exists():
            target_image_path.unlink()
'''
                for i, line in enumerate(lines):
                    if '__all__ = (' in line:
                        lines.insert(i - 1, uninstall_image_code)
                        changes_made = True
                        break
            
            old_text = "https://github.com/PortsMaster/PortMaster-Info/raw/main/"
            new_text = "https://github.com/PortsMaster/PortMaster-Info/blob/main/"
            
            if old_text in content:
                content = content.replace(old_text, new_text)
                changes_made = True
            
            if changes_made:
                with open(HARBOUR_FILE, "w") as f:
                    f.write("\n".join(lines))
            
            return True
        else:
            return True
            
    except Exception as e:
        logger.error(f"Ошибка обновления конфигурации: {str(e)}")
        return False

def other_update():
    try:
        default_ttf = os.path.join(LEGACY_PORTMASTER_DIR, "default.ttf")
        if not os.path.exists(default_ttf):
            try:
                shutil.copy2("/mnt/vendor/bin/default.ttf", default_ttf)
            except Exception as e:
                logger.error(f"Ошибка копирования default.ttf: {e}")
                return False
        
        resources_dir = os.path.join(LEGACY_PORTMASTER_DIR, "pylibs/resources")
        try:
            os.makedirs(resources_dir, exist_ok=True)
            os.chmod(resources_dir, 0o755)
        except Exception as e:
            logger.error(f"Ошибка создания директории resources: {e}")
            return False
        
        noto_archive = os.path.join(resources_dir, "NotoSans.tar.xz")
        if os.path.exists(noto_archive):
            try:
                import tarfile
                with tarfile.open(noto_archive, 'r:xz') as tar:
                    tar.extractall(path=resources_dir)
                os.remove(noto_archive)
                logger.info("NotoSans.tar.xz успешно распакован")
            except Exception as e:
                logger.error(f"Ошибка распаковки NotoSans.tar.xz: {e}")
                return False
        
        noto_font_link = os.path.join(resources_dir, "NotoSansSC-Regular.ttf")
        if os.path.exists(noto_font_link):
            try:
                os.remove(noto_font_link)
            except Exception as e:
                logger.error(f"Ошибка удаления символической ссылки: {e}")
                return False
        try:
            os.symlink(default_ttf, noto_font_link)
            os.chmod(noto_font_link, 0o644)
        except Exception as e:
            logger.error(f"Ошибка создания символической ссылки: {e}")
            return False

        
        pugwash_file = os.path.join(LEGACY_PORTMASTER_DIR, "pugwash.txt")
        if os.path.exists(pugwash_file):
            try:
                os.remove(pugwash_file)
            except Exception as e:
                logger.error(f"Ошибка удаления pugwash.txt: {e}")
                return False
            
        ports_fix()
        
        return True
    except Exception as e:
        logger.error(f"Общая ошибка в other_update: {e}")
        return False

def clean_exit(*args):
    logger.info("Начало clean_exit...")
    
    logger.info("Очистка временных файлов...")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    try:
        logger.info("Настройка библиотек...")
        for path in glob.glob('/usr/lib/aarch64-linux-gnu/libEGL.so*'):
            subprocess.run(["sudo", "rm", "-f", path], check=True)
        for path in glob.glob('/usr/lib/aarch64-linux-gnu/libGLES*'):
            subprocess.run(["sudo", "rm", "-f", path], check=True)
        subprocess.run(["sudo", "ln", "-sf", "/usr/lib/libmali.so", "/usr/lib/aarch64-linux-gnu/libEGL.so.1"], check=True)
        subprocess.run(["sudo", "ln", "-sf", "/usr/lib/libmali.so", "/usr/lib/aarch64-linux-gnu/libGLESv2.so.2"], check=True)
        subprocess.run(["sudo", "cp", "-f", "/lib/arm-linux-gnueabihf/libfreetype.so.6", "/mnt/vendor/lib/libfreetype.so.6.8.0"], check=True)
        subprocess.run(["sudo", "ln", "-sf", "/usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0.2800.5", "/usr/lib/libSDL2-2.0.so.0"], check=True)
        subprocess.run(["sudo", "ldconfig"], check=True)
        logger.info("Библиотеки настроены успешно")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при настройке библиотек: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при настройке библиотек: {str(e)}")

    logger.info("Проверка PortMaster.sh...")
    portmaster_sh = os.path.join(LEGACY_PORTMASTER_DIR, "PortMaster.sh")
    if os.path.exists(portmaster_sh):
        logger.info(f"Запуск PortMaster.sh: {portmaster_sh}")
        try:
            os.chmod(portmaster_sh, 0o755)
            os.execv(portmaster_sh, [portmaster_sh] + list(args))
        except PermissionError:
            logger.error("Ошибка: нет прав на выполнение PortMaster.sh")
            exit_program(translator.translate('Error'), 3)
    else:
        logger.error("Ошибка: PortMaster.sh не найден")
        exit_program(translator.translate('Error'), 3)

def check_port_master_version() -> bool:
    port_master_version = os.path.join(LEGACY_PORTMASTER_DIR, "version")
    
    try:

        socket.setdefaulttimeout(10)
        with urllib.request.urlopen(GITHUB_API_URL) as response:
            release_info = json.loads(response.read().decode())
            global port_master_github_version
            port_master_github_version = release_info.get("tag_name", "")
            logger.info(f"Получена версия с GitHub: {port_master_github_version}")
        
        if not port_master_github_version:
            logger.error("Не удалось получить версию с GitHub")
            return True
            
        if not os.path.exists(port_master_version):
            return False
            
        with open(port_master_version, "r") as f:
            current_version = f.read().strip()
        
        logger.info(f"Сравниваем версии: текущая={current_version}, github={port_master_github_version}")
        if current_version != port_master_github_version:
            return False
        else:
            return True
            
    except Exception as e:
        logger.error(f"Ошибка проверки версии: {str(e)}")
        return True
    
def load_screen_show_update_prompt() -> bool:
    global selected_position, selected_system, skip_input_check

    gr.draw_clear()
    gr.draw_text((x_size / 2, y_size / 2 - 60), translator.translate('New version of PortMaster is available'), font=17, anchor="mm")
    gr.draw_text((x_size / 2, y_size / 2 - 30), translator.translate('Do you want to update?'), font=13, anchor="mm")
    button_rectangle((x_size / 2 - 140, y_size / 2 + 60), "A", f"{translator.translate('Yes')}")
    button_rectangle((x_size / 2 + 70, y_size / 2 + 60), "B", f"{translator.translate('No')}")
    
    gr.draw_paint()
    
    waiting = True
    while waiting:
        input.check()
        if input.key("A"):
            waiting = False
            return True
        elif input.key("B"):
            waiting = False
            return False
    
    input.reset_input()
    return False    

def load_screen_update_port_master() -> None:
    global selected_position, selected_system, skip_input_check, port_master_github_version

    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    def show_download_progress(block_num, block_size, total_size):
        if block_num % 10 != 0 and block_num < 100:
            return

        try:
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                
                gr.draw_clear()
                gr.draw_text((x_size / 2, y_size / 2 - 60), translator.translate('Downloading PortMaster...'), font=17, anchor="mm")
                gr.draw_text((x_size / 2, y_size / 2 - 30), translator.translate('Downloading the update'), font=13, anchor="mm")
                
                bar_width = x_size - 100
                gr.draw_rectangle([50, y_size / 2 + 20, 50 + bar_width, y_size / 2 + 40], fill=gr.colorGrayL1)
                
                filled_width = int(bar_width * percent / 100)
                if filled_width > 0:
                    gr.draw_rectangle([50, y_size / 2 + 20, 50 + filled_width, y_size / 2 + 40], fill=gr.colorBlue)
                
                gr.draw_text((x_size / 2, y_size / 2 + 30), f"{int(percent)}%", font=13, anchor="mm")
                gr.draw_paint()
        except Exception as e:
            logger.error(f"Ошибка отображения прогресса: {str(e)}")

    try:
        gr.draw_clear()
        gr.draw_text((x_size / 2, y_size / 2 - 60), translator.translate('Downloading PortMaster...'), font=17, anchor="mm")
        gr.draw_paint()
        
        socket.setdefaulttimeout(30)
        urllib.request.urlretrieve(GITHUB_DOWNLOAD_URL, TEMP_FILE, show_download_progress)
        
        gr.draw_clear()
        gr.draw_text((x_size / 2, y_size / 2 - 60), translator.translate('Unpacking the PortMaster...'), font=17, anchor="mm")
        gr.draw_paint()
        
        libs_exists = False
        if os.path.exists(LEGACY_PORTMASTER_DIR):
            libs_dir = os.path.join(LEGACY_PORTMASTER_DIR, "libs")
            libs_exists = os.path.exists(libs_dir)
            for item in os.listdir(LEGACY_PORTMASTER_DIR):
                if item != "libs":
                    item_path = os.path.join(LEGACY_PORTMASTER_DIR, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
        
        with zipfile.ZipFile(TEMP_FILE, 'r') as zip_ref:
            total_files = len(zip_ref.namelist())
            for i, file in enumerate(zip_ref.namelist()):
                if "libs/" in file:
                    continue
                    
                zip_ref.extract(file, TEMP_DIR)
                
                percent = (i + 1) * 100 / total_files
                gr.draw_clear()
                gr.draw_text((x_size / 2, y_size / 2 - 60), translator.translate('Unpacking the PortMaster...'), font=17, anchor="mm")
                gr.draw_text((x_size / 2, y_size / 2 - 30), f"{translator.translate('File')}: {os.path.basename(file)}", font=13, anchor="mm")
                
                bar_width = x_size - 100
                gr.draw_rectangle([50, y_size / 2 + 20, 50 + bar_width, y_size / 2 + 40], fill=gr.colorGrayL1)
                
                filled_width = int(bar_width * percent / 100)
                if filled_width > 0:
                    gr.draw_rectangle([50, y_size / 2 + 20, 50 + filled_width, y_size / 2 + 40], fill=gr.colorBlue)
                
                gr.draw_text((x_size / 2, y_size / 2 + 30), f"{int(percent)}%", font=13, anchor="mm")
                gr.draw_paint()
        
        portmaster_dir = os.path.join(TEMP_DIR, "PortMaster")
        if os.path.isdir(portmaster_dir):
            for item in os.listdir(portmaster_dir):
                src = os.path.join(portmaster_dir, item)
                dst = os.path.join(LEGACY_PORTMASTER_DIR, item)
                if item == "libs" and libs_exists:
                    continue
                shutil.move(src, dst)
            os.rmdir(portmaster_dir)

        pylibs_zip = os.path.join(LEGACY_PORTMASTER_DIR, "pylibs.zip")
        if os.path.exists(pylibs_zip):
            try:
                with zipfile.ZipFile(pylibs_zip, 'r') as zip_ref:
                    zip_ref.extractall(LEGACY_PORTMASTER_DIR)
                os.remove(pylibs_zip)
                logger.info("pylibs.zip успешно распакован")
            except Exception as e:
                logger.error(f"Ошибка при распаковке pylibs.zip: {e}")
        
        for root, _, files in os.walk(LEGACY_PORTMASTER_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(('.sh', '.py')) or file == 'PortMaster':
                    os.chmod(file_path, 0o755)
                elif 'runtimes' in root and file.endswith('.aarch64'):
                    os.chmod(file_path, 0o755)
                    try:
                        subprocess.run(['sudo', 'chmod', '755', file_path], check=True)
                        logger.info(f"Установлены права на {file} через sudo")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Ошибка установки прав через sudo на {file}: {e}")
        
        version_file = os.path.join(LEGACY_PORTMASTER_DIR, "version")
        with open(version_file, "w") as f:
            f.write(port_master_github_version)
            logger.info(f"Сохранена версия: {port_master_github_version}")
        
        os.remove(TEMP_FILE)
        shutil.rmtree(TEMP_DIR)

        os.environ['LANG'] = system_lang
        os.environ['LANGUAGE'] = system_lang
        os.environ['LC_ALL'] = system_lang
        os.environ['LC_MESSAGES'] = system_lang

        gr.draw_clear()
        gr.draw_text((x_size / 2, y_size / 2), translator.translate('Update completed'), font=17, anchor="mm")
        gr.draw_paint()

        time.sleep(3)

    except Exception as e:
        logger.error(f"Ошибка обновления: {str(e)}")
        exit_program(translator.translate('Error'), 3)

def check_runtimes_version() -> bool:
    libs_dir = os.path.join(LEGACY_PORTMASTER_DIR, "libs")
    os.makedirs(libs_dir, exist_ok=True)

    try:
        socket.setdefaulttimeout(10)
        with urllib.request.urlopen(RUNTIMES_API_URL) as response:
            release_info = json.loads(response.read().decode())

        download_urls = [asset["browser_download_url"] for asset in release_info.get("assets", [])]
        if not download_urls:
            logger.error("Не найдены файлы для скачивания в релизе рантаймов")
            return False

        installed_files = set(os.listdir(libs_dir)) if os.path.exists(libs_dir) else set()
        
        missing_files = []
        for url in download_urls:
            filename = os.path.basename(url)
            if filename not in installed_files:
                missing_files.append(url)

        if not missing_files:
            logger.info("Все файлы рантаймов установлены")
            return True

        logger.info(f"Найдено {len(missing_files)} отсутствующих файлов рантаймов")
        return False

    except urllib.error.URLError as e:
        logger.error(f"Ошибка при проверке версии рантаймов: {e.reason}")
        return False
    except socket.timeout:
        logger.error("Таймаут при проверке версии рантаймов")
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки рантаймов: {str(e)}")
        return False

def load_creen_runtimes() -> None:
    global selected_position, selected_system, skip_input_check

    gr.draw_clear()
    gr.draw_text((x_size / 2, y_size / 2 - 30), translator.translate('Do you want to download runtimes for PortMaster?'), font=17, anchor="mm")
    button_rectangle((x_size / 2 - 140, y_size / 2 + 60), "A", f"{translator.translate('Yes')}")
    button_rectangle((x_size / 2 + 70, y_size / 2 + 60), "B", f"{translator.translate('No')}")
    
    gr.draw_paint()
    
    waiting = True
    while waiting:
        input.check()
        if input.key("A"):
            waiting = False
            load_screen_process_download_runtimes()
        elif input.key("B"):
            waiting = False
            return
    
    input.reset_input()

def load_screen_process_download_runtimes() -> None:
    global selected_position, selected_system, skip_input_check

    temp_dir = "/tmp/PortMaster_Runtime_Update"
    libs_dir = os.path.join(LEGACY_PORTMASTER_DIR, "libs")

    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(libs_dir, exist_ok=True)

    try:
        with urllib.request.urlopen(RUNTIMES_API_URL) as response:
            release_info = json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"Ошибка получения информации о рантаймах: {e}")
        return

    download_urls = [asset["browser_download_url"] for asset in release_info.get("assets", [])]
    if not download_urls:
        logger.error("Не удалось получить URL для скачивания рантаймов")
        return

    installed_files = set(os.listdir(libs_dir)) if os.path.exists(libs_dir) else set()
    
    missing_files = []
    for url in download_urls:
        filename = os.path.basename(url)
        if filename not in installed_files:
            missing_files.append(url)

    if not missing_files:
        gr.draw_clear()
        gr.draw_text((x_size / 2, y_size / 2), "Все файлы рантаймов уже установлены", font=17, anchor="mm")
        gr.draw_paint()
        time.sleep(3)
        return

    success_count = 0
    total_files = len(missing_files)
    failed_files = []
    current_filename = ""
    
    def show_progress(block_num, block_size, total_size):
        nonlocal current_filename
        
        if block_num % 10 != 0 and block_num < 100:
            return
        
        try:
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                
                gr.draw_clear()
                gr.draw_text((x_size / 2, y_size / 2 - 60), f"{translator.translate('Downloading runtimes...')}", font=17, anchor="mm")
                gr.draw_text((x_size / 2, y_size / 2 - 30), f"{translator.translate('File')}: {current_filename}", font=13, anchor="mm")
                gr.draw_text((x_size / 2, y_size / 2), f"{translator.translate('Progress')}: {success_count+1}/{total_files}", font=13, anchor="mm")
                
                bar_width = x_size - 100
                gr.draw_rectangle([50, y_size / 2 + 20, 50 + bar_width, y_size / 2 + 40], fill=gr.colorGrayL1)
                
                filled_width = int(bar_width * percent / 100)
                if filled_width > 0:
                    gr.draw_rectangle([50, y_size / 2 + 20, 50 + filled_width, y_size / 2 + 40], fill=gr.colorBlue)
                
                gr.draw_text((x_size / 2, y_size / 2 + 30), f"{int(percent)}%", font=13, anchor="mm")
                gr.draw_paint()
        except Exception as e:
            logger.error(f"Ошибка в функции обратного вызова: {str(e)}")

    for i, url in enumerate(missing_files):
        current_filename = os.path.basename(url)
        output_file = os.path.join(temp_dir, current_filename)
        
        try:
            gr.draw_clear()
            gr.draw_text((x_size / 2, y_size / 2 - 60), f"{translator.translate('Downloading runtimes...')}", font=17, anchor="mm")
            gr.draw_text((x_size / 2, y_size / 2 - 30), f"{translator.translate('File')}: {current_filename}", font=13, anchor="mm")
            gr.draw_text((x_size / 2, y_size / 2), f"{translator.translate('Progress')}: {i+1}/{total_files}", font=13, anchor="mm")
            gr.draw_rectangle([50, y_size / 2 + 20, 50 + (x_size - 100), y_size / 2 + 40], fill=gr.colorGrayL1)
            gr.draw_text((x_size / 2, y_size / 2 + 30), "0%", font=13, anchor="mm")
            gr.draw_paint()
            
            socket.setdefaulttimeout(30)
            urllib.request.urlretrieve(url, output_file, show_progress)
            
            file_size = os.path.getsize(output_file)
            
            if file_size > 1000:
                logger.info(f"Успешно скачан: {current_filename} ({file_size} байт)")
                success_count += 1
            else:
                logger.warning(f"Файл {current_filename} слишком мал или пуст ({file_size} байт), пропускаем")
                os.remove(output_file)
                failed_files.append(current_filename)
                
        except urllib.error.URLError as e:
            err_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            logger.error(f"Ошибка скачивания {current_filename}: {err_msg}")
            failed_files.append(current_filename)
        except socket.timeout:
            logger.error(f"Таймаут при скачивании {current_filename}")
            failed_files.append(current_filename)
        except Exception as e:
            logger.error(f"Ошибка скачивания {current_filename}: {str(e)}")
            failed_files.append(current_filename)
    
    if success_count > 0:
        for filename in os.listdir(temp_dir):
            src = os.path.join(temp_dir, filename)
            dst = os.path.join(libs_dir, filename)
            shutil.copy2(src, dst)
            os.chmod(dst, 0o644)  
    
    try:
        gr.draw_clear()
        if success_count > 0:
            gr.draw_text((x_size / 2, y_size / 2), f"{translator.translate('Downloaded files')}: {success_count} {translator.translate('Of')} {total_files}", font=17, anchor="mm")
            
            if failed_files:
                gr.draw_text((x_size / 2, y_size / 2 - 30), f"{translator.translate('Failed to download')} {len(failed_files)} {translator.translate('Files')}", font=13, anchor="mm")
                
                if len(failed_files) <= 5:
                    failed_str = ", ".join(failed_files)
                    if len(failed_str) > 60:
                        failed_str = failed_str[:57] + "..."
                    gr.draw_text((x_size / 2, y_size / 2), failed_str, font=11, anchor="mm")
        else:
            gr.draw_text((x_size / 2, y_size / 2 - 30), f"{translator.translate('Failed to download runtimes')}", font=17, anchor="mm")
            logger.error("Не удалось скачать рантаймы")

        gr.draw_paint()
        time.sleep(3)
    except Exception as e:
        logger.error(f"Ошибка при отображении результатов: {str(e)}")
    
    shutil.rmtree(temp_dir, ignore_errors=True)

def ports_fix():
    try:
        controlfolder = "/roms/ports/PortMaster"
        device_info_txt = f"{controlfolder}/device_info.txt"
        funcs_txt = f"{controlfolder}/funcs.txt"
        control_txt = f"{controlfolder}/control.txt"
        gamecontrollerdb_txt = f"{controlfolder}/gamecontrollerdb.txt"
        libgl_Stock_txt = f"{controlfolder}/libgl_Ubuntu.txt"
        mod_Stock_txt = f"{controlfolder}/mod_Ubuntu.txt"
        stock_path = f"{controlfolder}/Ubuntu"
        global fix_flg_grh

        def insert_lines_after(filename, search, lines):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.readlines()
                for idx, line in enumerate(content):
                    if search in line:
                        break
                else:
                    return False
                idx += 1
                for l in reversed(lines):
                    content.insert(idx, l + '\n')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.writelines(content)
                return True
            except Exception as e:
                logger.error(f"Ошибка при вставке строк в {filename}: {e}")
                return False

        if os.path.isfile(device_info_txt):
            with open(device_info_txt, encoding='utf-8') as f:
                if fix_flg_grh not in f.read():
                    with open(device_info_txt, 'r', encoding='utf-8') as f2:
                        lines = f2.readlines()
                    lines.insert(1, f"# {fix_flg_grh}\n")
                    with open(device_info_txt, 'w', encoding='utf-8') as f2:
                        f2.writelines(lines)
                    search = 'DEVICE_NAME=$(cat /storage/.config/device)'
                    block = [
                        '    elif [[ "$CFW_NAME" == "Ubuntu" ]] && [[ -f "/mnt/vendor/oem/board.ini" ]]; then',
                        '        declare -A device_name_mapping=(',
                        '            ["RG28xx"]="RG28XX-H"',
                        '            ["RG34xx"]="RG34XX-H"',
                        '            ["RG34xxSP"]="RG34XX-SP"',
                        '            ["RG35xx+_P"]="RG35XX-PLUS"',
                        '            ["RG35xxH"]="RG35XX-H"',
                        '            ["RG35xxPRO"]="RG35XX-PRO"',
                        '            ["RG35xxSP"]="RG35XX-SP"',
                        '            ["RG40xxH"]="RG40XX-H"',
                        '            ["RG40xxV"]="RG40XX-V"',
                        '            ["RGcubexx"]="RGCUBEXX-H"',
                        '        )',
                        '        DEVICE_NAME=$(cat /mnt/vendor/oem/board.ini)',
                        '        DEVICE_NAME=${device_name_mapping[$DEVICE_NAME]}'
                    ]
                    if not insert_lines_after(device_info_txt, search, block):
                        logger.error("Ошибка при обновлении device_info.txt")
                        return False

        if os.path.isfile(control_txt):
            with open(control_txt, encoding='utf-8') as f:
                if fix_flg_grh not in f.read():
                    with open(control_txt, 'r', encoding='utf-8') as f2:
                        lines = f2.readlines()
                    lines.insert(1, f"# {fix_flg_grh}\n")
                    lines = [l.replace('    DEVICE="${1}"', '    DEVICE="19000000010000000100000000010000"') for l in lines]
                    lines = [l.replace('param_device="${2}"', '    param_device="anbernic"') for l in lines]
                    with open(control_txt, 'w', encoding='utf-8') as f2:
                        f2.writelines(lines)
                    heredoc = '''
CUR_TTY=/dev/null
export HOME="/root"
mkdir -p ~/.local/share
mkdir -p ~/.config
controlfolder="/roms/ports/PortMaster"

SH_DIR="$(cd $(dirname "$0"); pwd)"
directory="mnt/$(echo "$SH_DIR" | cut -d '/' -f3)/Roms"

DSIPLAY_ID="$(cat /sys/class/power_supply/axp2202-battery/display_id)"
if [[ $DSIPLAY_ID == "1" ]]; then
  AUDIODEV=hw:2,0
else
  if [ -f "/roms/lib64/libSDL2-2.0.so.0.2800.6" ]; then
    LD_PRELOAD=/roms/lib64/libSDL2-2.0.so.0.2800.6
  fi
fi
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib32
raloc="/mnt/vendor/deep/retro"
raconf="--config /.config/retroarch/retroarch.cfg"
if [[ -e "/dev/input/by-path/platform-soc@03000000:gpio_keys-event-joystick" ]]; then
    echo 1 > /sys/class/power_supply/axp2202-battery/nds_esckey
    dpid=`ps -A| grep "portsCtrl.dge"| awk 'NR==1{print $1}'`
    if [ ${dpid} ]; then
        echo "had run portsCtrl.dge"
    else
        /mnt/vendor/bin/portsCtrl.dge &
    fi
fi
'''
                    with open(control_txt, 'a', encoding='utf-8') as f2:
                        f2.write(heredoc)

        if os.path.isfile(gamecontrollerdb_txt):
            with open(gamecontrollerdb_txt, encoding='utf-8') as f:
                if fix_flg_grh not in f.read():
                    heredoc = '''
# make by G.R.H
19000000010000000100000000010000,ANBERNIC-keys,a:b0,b:b1,x:b3,y:b2,back:b8,guide:b6,start:b7,leftstick:b9,rightstick:b12,leftshoulder:b4,rightshoulder:b5,dpup:h0.1,dpleft:h0.8,dpdown:h0.4,dpright:h0.2,leftx:a0,lefty:a1,rightx:a2,righty:a3,lefttrigger:b10,righttrigger:b11,platform:Linux,
'''
                    with open(gamecontrollerdb_txt, 'a', encoding='utf-8') as f2:
                        f2.write(heredoc)

        if not os.path.isfile(mod_Stock_txt):
            heredoc = '''#!/bin/bash
#
# SPDX-License-Identifier: MIT
#
## Modular - STOCKOS
# 
# A modular file that is sourced for specific script lines required by ports running on STOCKOS.
#
# usage `[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"`
# Set the virtual screen
CUR_TTY="/dev/null"
# Use for Godot 2
GODOT2_OPTS="-r ${DISPLAY_WIDTH}x${DISPLAY_HEIGHT} -f"
# Use for Godot 3+
GODOT_OPTS="--resolution ${DISPLAY_WIDTH}x${DISPLAY_HEIGHT} -f"
pm_platform_helper() {
    # Help keep XongleBongles sanity below
    echo ""
}
'''
            with open(mod_Stock_txt, 'w', encoding='utf-8') as f:
                f.write(heredoc)

        if not os.path.isfile(libgl_Stock_txt):
            heredoc = '''#!/bin/bash
#
# SPDX-License-Identifier: MIT
#
# NOTE: This script uses $PWD to setup the GL4ES directory!
# Before calling this, ensure you are on the port root directory, e.g.:
# > gamedir="/$directory/ports/stardewvalley"
# > cd "$gamedir/"
export LIBGL_ES=2
export LIBGL_GL=21
export LIBGL_FB=3
# If the dri device does not exist, then let's not use
# the gbm backend.
if [ ! -e "/dev/dri/card0" ]; then
  export LIBGL_FB=2
fi
if [ -d "$PWD/gl4es.$DEVICE_ARCH" ]; then
  export LD_LIBRARY_PATH="$PWD/gl4es.$DEVICE_ARCH:$LD_LIBRARY_PATH"
elif [ -d "$PWD/gl4es" ]; then
  export LD_LIBRARY_PATH="$PWD/gl4es:$LD_LIBRARY_PATH"
fi
# This sets up the standard libs directory.
if [ -d "$PWD/libs.$DEVICE_ARCH" ]; then
  export LD_LIBRARY_PATH="$PWD/libs.$DEVICE_ARCH:$LD_LIBRARY_PATH"
elif [ -d "$PWD/libs" ]; then
  export LD_LIBRARY_PATH="$PWD/libs:$LD_LIBRARY_PATH"
fi
'''
            with open(libgl_Stock_txt, 'w', encoding='utf-8') as f:
                f.write(heredoc)

        if not os.path.isdir(stock_path):
            os.makedirs(stock_path, exist_ok=True)
            shutil.copy2(control_txt, stock_path)
            shutil.copy2(gamecontrollerdb_txt, stock_path)
            heredoc = '''#!/bin/bash
# make by G.R.H
#
# SPDX-License-Identifier: MIT
#
## HRMMM
export HOME="/root"
DSIPLAY_ID="$(cat /sys/class/power_supply/axp2202-battery/display_id)"
if [[ $DSIPLAY_ID == "1" ]]; then
  AUDIODEV=hw:2,0
else
  if [ -f "/roms/lib64/libSDL2-2.0.so.0.2800.6" ]; then
    LD_PRELOAD=/roms/lib64/libSDL2-2.0.so.0.2800.6
  fi
fi
controlfolder="/roms/ports/PortMaster"
SH_DIR="$(cd $(dirname "$0"); pwd)"
directory="mnt/$(echo "$SH_DIR" | cut -d '/' -f3)/Roms"
# MIYOO_EXtra shit i need.
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib32
ESUDO=""
ESUDOKILL="-1" # for 351Elec and EmuELEC use "-1" (numeric one) or "-k" 
export SDL_GAMECONTROLLERCONFIG_FILE="/usr/lib/gamecontrollerdb.txt"
# export SDL_GAMECONTROLLERCONFIG=$(grep "Deeplay" "/usr/lib/gamecontrollerdb.txt")
source "$controlfolder/device_info.txt"
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
## TODO: Change to PortMaster/tty when Johnnyonflame merges the changes in,
CUR_TTY=/dev/null
cd "$controlfolder"
exec > >(tee "$controlfolder/log.txt") 2>&1
source "$controlfolder/utils/pmsplash.txt"
## Autoinstallation Code
# This will automatically install zips found within the PortMaster/autoinstall directory using harbourmaster
AUTOINSTALL=$(find "$controlfolder/autoinstall" -type f \( -name "*.zip" -o -name "*.squashfs" \))
if [ -n "$AUTOINSTALL" ]; then
  source "$controlfolder/PortMasterDialog.txt"
  GW=$(PortMasterIPCheck)
  PortMasterDialogInit "no-check"
  PortMasterDialog "messages_begin"
  PortMasterDialog "message" "Auto-installation"
  # Install the latest runtimes.zip
  if [ -f "$controlfolder/autoinstall/runtimes.zip" ]; then
    PortMasterDialog "message" "- Installing runtimes.zip, this could take a minute or two."
    $ESUDO unzip -o "$controlfolder/autoinstall/runtimes.zip" -d "$controlfolder/libs"
    $ESUDO rm -f "$controlfolder/autoinstall/runtimes.zip"
    PortMasterDialog "message" "- SUCCESS: runtimes.zip"
  fi
  for file_name in "$controlfolder/autoinstall"/*.squashfs
  do
    if [ ! -f "$file_name" ]; then
      continue
    fi
    $ESUDO mv -f "$file_name" "$controlfolder/libs"
    PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
  done
  for file_name in "$controlfolder/autoinstall"/*.zip
  do
    if [ ! -f "$file_name" ]; then
      continue
    fi
    if [[ "$(basename $file_name)" == "PortMaster.zip" ]]; then
      continue
    fi
    if [[ $(PortMasterDialogResult "install" "$file_name") == "OKAY" ]]; then
      $ESUDO rm -f "$file_name"
      PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
    else
      PortMasterDialog "message" "- FAILURE: $(basename $file_name)"
    fi
    touch "$controlfolder/.muos-refresh"
  done
  if [ -f "$controlfolder/autoinstall/PortMaster.zip" ]; then
    if [ ! -f "$file_name" ]; then
      continue
    fi
    file_name="$controlfolder/autoinstall/PortMaster.zip"
    if [[ $(PortMasterDialogResult "install" "$file_name") == "OKAY" ]]; then
      $ESUDO rm -f "$file_name"
      PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
    else
      PortMasterDialog "message" "- FAILURE: $(basename $file_name)"
    fi
  fi
  PortMasterDialog "messages_end"
  if [ -z "$GW" ]; then
    PortMasterDialogMessageBox "Finished running autoinstall.\n\nNo internet connection present so exiting."
    PortMasterDialogExit
    exit 0
  else
    PortMasterDialogMessageBox "Finished running autoinstall."
    PortMasterDialogExit
  fi
fi
export TERM=linux
# # Do it twice, it's just as nice!
# cat /dev/zero > /dev/fb0 2>/dev/null
# cat /dev/zero > /dev/fb0 2>/dev/null
pm_message "Starting PortMaster."
$ESUDO chmod -R +x .
unset LD_LIBRARY_PATH
unset SDL_GAMECONTROLLERCONFIG
PATH="$OLD_PATH"
'''
            with open(os.path.join(stock_path, "PortMaster.txt"), 'w', encoding='utf-8') as f:
                f.write(heredoc)

        logger.info("Скрипт ports_fix успешно выполнен")
        return True

    except Exception as e:
        logger.error(f"Ошибка в ports_fix: {e}")
        return False

def set_portmaster_language():
    LANG_FILE = os.path.join(LEGACY_PORTMASTER_DIR, "config", "config.json")

    try:
        if system_lang == 'zh_TW':
            set_lang = 'zh_CN'
        else:
            set_lang = system_lang

        if not os.path.exists(LANG_FILE):
            logger.info("Файл конфигурации не существует, никаких действий не требуется.")
            return 0
        
        if not os.access(LANG_FILE, os.R_OK | os.W_OK):
            logger.error(f"Отсутствуют права доступа к файлу: {LANG_FILE}")

        with open(LANG_FILE, 'r') as f:
            try:
                config_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Неверный формат JSON: {str(e)}")

        modified = False
        
        if 'language' in config_data:
            if config_data['language'] != set_lang:
                config_data['language'] = set_lang
                modified = True
                
        else:
            config_data['language'] = set_lang
            modified = True

        if modified:
            temp_fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(LANG_FILE),
                suffix='.tmp',
                text=True
            )
            
            try:
                with os.fdopen(temp_fd, 'w') as temp_file:
                    json.dump(config_data, temp_file, indent=4, ensure_ascii=False)
                
                shutil.move(temp_path, LANG_FILE)
                logger.info("Настройки языка успешно обновлены")
                
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                logger.error(f"Запись не удалась: {str(e)}")

        return 0

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return 1

def update() -> None:
    global selected_position, skip_input_check

    if skip_input_check:
        input.reset_input()
        skip_input_check = False
    else:
        input.check()

    if input.key("MENUF"):
        gr.draw_end()
        sys.exit()

def button_circle(pos: tuple[int, int], button: str, text: str) -> None:
    gr.draw_circle(pos, 25, fill=gr.colorBlueD1)
    gr.draw_text((pos[0] + 12, pos[1] + 12), button, anchor="mm")
    gr.draw_text((pos[0] + 30, pos[1] + 12), text, font=13, anchor="lm")

def button_rectangle(pos: tuple[int, int], button: str, text: str) -> None:
    gr.draw_rectangle_r(
        (pos[0], pos[1], pos[0] + 60, pos[1] + 25), 5, fill=gr.colorGrayL1
    )
    gr.draw_text((pos[0] + 30, pos[1] + 12), button, anchor="mm")
    gr.draw_text((pos[0] + 65, pos[1] + 12), text, font=13, anchor="lm")