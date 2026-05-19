# -*- coding: utf-8 -*-
import os
from configparser import ConfigParser


class ConfigManager:
    def __init__(self):
        self.config = ConfigParser()
        self.encrypt_last_path = ""
        self.decrypt_last_path = ""
        self._init_config()

    def _get_config_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user.ini')

    def _init_config(self):
        config_path = self._get_config_path()

        try:
            if not os.path.exists(config_path):
                self.config['Paths'] = {
                    'encrypt_last_path': '',
                    'decrypt_last_path': ''
                }
                self._save_config()
            else:
                self._load_config()
        except Exception as e:
            print(f"警告：配置文件初始化失败 - {str(e)}")
            self.encrypt_last_path = ""
            self.decrypt_last_path = ""

    def _load_config(self):
        config_path = self._get_config_path()

        try:
            self.config.read(config_path, encoding='utf-8')

            if 'Paths' in self.config:
                self.encrypt_last_path = self.config['Paths'].get('encrypt_last_path', '')
                self.decrypt_last_path = self.config['Paths'].get('decrypt_last_path', '')
            else:
                self.encrypt_last_path = ""
                self.decrypt_last_path = ""
        except Exception as e:
            print(f"警告：读取配置文件失败 - {str(e)}")
            self.encrypt_last_path = ""
            self.decrypt_last_path = ""

    def _save_config(self):
        config_path = self._get_config_path()

        try:
            if 'Paths' not in self.config:
                self.config['Paths'] = {}

            self.config['Paths']['encrypt_last_path'] = self.encrypt_last_path
            self.config['Paths']['decrypt_last_path'] = self.decrypt_last_path

            with open(config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"警告：保存配置文件失败 - {str(e)}")

    def _update_encrypt_path(self, file_path):
        if file_path:
            dir_path = os.path.dirname(file_path)
            if dir_path and os.path.exists(dir_path):
                self.encrypt_last_path = dir_path
                self._save_config()

    def _update_decrypt_path(self, file_path):
        if file_path:
            dir_path = os.path.dirname(file_path)
            if dir_path and os.path.exists(dir_path):
                self.decrypt_last_path = dir_path
                self._save_config()

    def get_encrypt_last_path(self):
        return self.encrypt_last_path

    def get_decrypt_last_path(self):
        return self.decrypt_last_path
