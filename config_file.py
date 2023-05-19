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

    def clear(self):
        self.config.clear()

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

class CfgSectionWrapper:
    def __init__(self, cfgFile: ConfigFile, sectionName: str):
        self._name = sectionName
        self._cfgFile = cfgFile

    def flush(self):
        self._cfgFile.write()

    def getName(self):
        return self._name

    def getPassword(self):
        return self._cfgFile.getParam(self._name, ConfigSchema.PARAM_NAME_PASSWORD)

    def setPassword(self, val: str):
        self._cfgFile.setParam(self._name, ConfigSchema.PARAM_NAME_PASSWORD, val)
    
    def getAllowed(self):
        strVal = self._cfgFile.getParam(self._name, ConfigSchema.PARAM_NAME_ALLOWED)
        return strVal.lower() in ['true', '1', 'y', 'yes']
    
    def setAllowed(self, val: bool):
        self._cfgFile.setParam(self._name, ConfigSchema.PARAM_NAME_ALLOWED, str(val))
    
    def getExecPath(self):
        return self._cfgFile.getParam(self._name, ConfigSchema.PARAM_NAME_EXEC_PATH)
    
    def setExecPath(self, val: str):
        return self._cfgFile.setParam(self._name, ConfigSchema.PARAM_NAME_EXEC_PATH, val)
    
    def getExecProcName(self):
        return self._cfgFile.getParam(self._name, ConfigSchema.PARAM_NAME_PROC_NAME)
    
    def setExecProcName(self, val: str):
        return self._cfgFile.setParam(self._name, ConfigSchema.PARAM_NAME_PROC_NAME, val)
    
def makeNewSection(configFile: ConfigFile, name: str) -> CfgSectionWrapper:
    configFile.config.add_section(name)
    configFile.config.set(name, ConfigSchema.PARAM_NAME_PASSWORD, '')
    configFile.config.set(name, ConfigSchema.PARAM_NAME_ALLOWED, '')
    configFile.config.set(name, ConfigSchema.PARAM_NAME_EXEC_PATH, '')
    configFile.config.set(name, ConfigSchema.PARAM_NAME_PROC_NAME, '')

    out = CfgSectionWrapper(configFile, name)
    out.setAllowed(False)
    out.setPassword('')
    out.setExecPath('')
    out.setExecProcName('')
    return out




