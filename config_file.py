import configparser

# Config file schema
class ConfigSchema:
    SECTION_NAME_SUPERUSER = "SUPERUSER"
    PARAM_NAME_PASSWORD = "password"
    PARAM_NAME_EXEC_PATH = "exec_path"
    PARAM_NAME_PROC_NAME = "proc_name"
    PARAM_NAME_ALLOWED = "allowed"

class ConfigFile:
    def read(path: str):
        config = configparser.ConfigParser()
        with open(path, mode='r', encoding='utf-8') as cfgFile:
            config.readfp(cfgFile)
            return ConfigFile(path, config)

    def __init__(self, path: str, config: configparser.ConfigParser):
        self.config = config
        self.path = path

    def getSections(self):
        return self.config.sections()

    def getParam(self, section: str, name: str):
        if section in self.config.sections():
            if name in self.config[section]:
                return self.config[section][name]
        return None
    
    def setParam(self, section: str, name: str, val):
        if section in self.config.sections():
            if name in self.config[section]:
                self.config[section][name] = val

    def write(self):
        with open(self.path, mode='w', encoding='utf-8') as cfgFile:
            self.config.write(cfgFile)



