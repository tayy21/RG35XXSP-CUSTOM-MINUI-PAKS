import app
from pathlib import Path

board_mapping = {
    'RGcubexx': 1,
    'RG34xx': 2,
    'RG34xxSP': 2,
    'RG28xx': 3,
    'RG35xx+_P': 4,
    'RG35xxH': 5,
    'RG35xxSP': 6,
    'RG40xxH': 7,
    'RG40xxV': 8,
    'RG35xxPRO': 9
}
system_list = ['zh_CN', 'zh_TW', 'en_US', 'ja_JP', 'ko_KR', 'es_LA', 'ru_RU', 'de_DE', 'fr_FR', 'pt_BR']

try:
    board_info = Path("/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
except (FileNotFoundError, IndexError):
    board_info = 'RG35xxH'
    
try:
    lang_info = Path("/mnt/vendor/oem/language.ini").read_text().splitlines()[0]
except (FileNotFoundError, IndexError):
    lang_info = 2

hw_info = board_mapping.get(board_info, 0)
system_lang = system_list[int(lang_info)]


def main():
    
    app.start()

    while True:
        app.update()

if __name__ == "__main__":
    main()
