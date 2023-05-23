import PySimpleGUI as sg
import os
import sys
import subprocess
from slave import SlaveClient
from config_file import ConfigFile, ConfigSchema, CfgSectionWrapper
from data import *
import re
import threading

lang = 1  # 0- enflish, 1 -rus

class Strings(enum.Enum):
    UNKNOWN = 0
    STR_OK = 1
    STR_BLOCKED = 2,
    STR_WRONG_PASSWORD = 3
    STR_ENTER_PWD = 4
    STR_PASSWORD = 5
    STR_TIME = 6
    STR_ACCESS_REQUEST = 7
    STR_STATUS = 8
    
LanguageMap = {
	Strings.UNKNOWN: ("UNKNOWN", "Ошибка"),
	Strings.STR_OK: ("OK", "ОК"),
	Strings.STR_BLOCKED: ("BLOCKED", "Заблокировано"),
	Strings.STR_WRONG_PASSWORD: ("Wrong password", "Неверный пароль"),
	Strings.STR_ENTER_PWD: ("Enter password", "Введите пароль"),
	Strings.STR_PASSWORD: ("Password: ", "Пароль: "),
	Strings.STR_TIME: ("Time: ", "Время: "),
	Strings.STR_ACCESS_REQUEST: ("Request access", "Запрашиваю разрешение"),
	Strings.STR_STATUS: ("Status: ", "Статус: "),
}

def getString(s: Strings):
	return LanguageMap[s][lang]

class App:
	# Path to config file
	#CONFIG_FILE_PATH = "C:\Games\game_wrapper\config.ini"
	CONFIG_FILE_PATH = "slave_config.ini"

	# Section to find in config. Came from start params
	gGameConfigName = "DEFAULT"

	# Build config
	gConfigFile: ConfigFile
	gGameConfig: CfgSectionWrapper

	gSuperUserMode = False

	gSlaveClient: SlaveClient

	gExit = False

	gGameStarted = False

	gTimeLimit = 0

	gStopThread: threading.Timer

	gElipces = ""

	gUserName = "User"

	def nextElipces():
		if len(App.gElipces) >= 3:
			App.gElipces = ""
		App.gElipces = App.gElipces + "."
		return App.gElipces

	window: sg.Window
	pwdButton = sg.Button("OK", key='pwdButtonId')
	pwdInput = sg.InputText(size=(65, 1), password_char='*', key='pwdInputId')
	timeInput = sg.InputText(size=(65, 1), key='timeInputId')
	statusLine = sg.InputText(size=(65, 1), key='statusInputId')

def setStatus(msg: str):
	print(f'Status: {msg}')
	try:
		App.window['statusInputId'].update(value=msg)
	except:
		pass

def onGameTimeout():
	print('GAME timeout!!!')
	stopGame()

def getStatistic():
	out = []
	try:
		for cfgName in App.gConfigFile.getSections():
			cfg = CfgSectionWrapper(App.gConfigFile, cfgName)
			with subprocess.Popen(f'tasklist /fi "USERNAME eq {App.gUserName}" /fi "IMAGENAME eq {cfg.getExecProcName()}"', stdout=subprocess.PIPE, shell=True, text=True, encoding='UTF-8') as proc:
				str, _ = proc.communicate()
				for line in str.splitlines():
					if cfg.getExecProcName() in line:
						out.append(cfg.getExecProcName())
						break
	except:
		out.append('system error')
	return out

def stopGame():
	setStatus(getString(Strings.STR_BLOCKED))
	proc_name = App.gGameConfig.getExecProcName()
	with subprocess.Popen(f'tasklist /fi "USERNAME eq {App.gUserName}" /fi "IMAGENAME eq {proc_name}"', stdout=subprocess.PIPE, shell=True, text=True, encoding='UTF-8') as proc:
		str, _ = proc.communicate()
		for line in str.splitlines():
			regExResult = re.findall('(?:.*\.exe) +([0-9]+)', line)
			if len(regExResult) > 0:
				proc_id = regExResult[0]
				print(f"kill {proc_id}")
				try:
					os.kill(int(proc_id), 9)
				except:
					print(f'Failed to stop PID {proc_id}')
		App.gSlaveClient.sendLogMessageRequest(f'game stopped [{App.gGameConfig.getName()}]')
	if App.gGameStarted:
		App.gExit = True
		App.pwdButton.click()

def startGame(byPassword: bool):
	gamePath = App.gGameConfig.getExecPath()
	if gamePath and App.gGameStarted == False:
		print('Start game!!!')
		App.gGameStarted = True
		os.startfile(gamePath)
		App.gSlaveClient.sendLogMessageRequest(f'game started [{App.gGameConfig.getName()}], by password: {str(byPassword)}')
		App.gSlaveClient.setConfigLoopPeriod(60)

def updateConfig(cfg_section: Data_ConfigSection):
	currCfg = CfgSectionWrapper(App.gConfigFile, cfg_section.name)
	if currCfg.getPassword() != cfg_section.pwd:
		currCfg.setPassword(cfg_section.pwd)
		currCfg.flush()

def checkConfig(cfg_section: Data_ConfigSection):
	if not App.gSuperUserMode and App.gGameConfig.getName() == cfg_section.name:
		if cfg_section.remote_accepted == False:
			stopGame()
		else:
			startGame(False)

def startStopTimer(timeoutSec: int):
	print(f'Start GAME timeout {timeoutSec} sec!!!')
	App.gStopThread = threading.Timer(timeoutSec, onGameTimeout)
	App.gStopThread.start()

def checkPassword(input_pwd: str):
	suCfg = CfgSectionWrapper(App.gConfigFile, ConfigSchema.SECTION_NAME_SUPERUSER)
	if input_pwd == suCfg.getPassword():
		return (True, True)
	config_pwd = App.gGameConfig.getPassword()
	if config_pwd:
		return (config_pwd == input_pwd, False)
	return (False, False)

def launchGameFromPassword(pwd: str):
	goodPwdFlag, superUserFlag = checkPassword(pwd)
	
	if superUserFlag:
		App.gSuperUserMode = True

	if goodPwdFlag:
		App.gSlaveClient.stopConfigRequestLoop()
	
	if goodPwdFlag or superUserFlag:
		startGame(True)
		timeLimit = App.timeInput.get()
		if len(timeLimit) == 0:
			timeLimit = '30'
		startStopTimer(int(timeLimit)*60)
	else:
		setStatus(getString(Strings.STR_WRONG_PASSWORD))
		print('Wrong password!!!')

def doAppLoop():
	def onMasterRequest(message):
		print(f'master request: {str(message)}')
		if message.msg_type == MessageType.MASTER_REQUEST_CONFIG_UPDATE:
			App.gSlaveClient.sendConfigUpdateReply(message)
			updateConfig(message.cfg_section)
			checkConfig(message.cfg_section)
		elif message.msg_type == MessageType.MASTER_REQUEST_CONFIG_LIST:
			out = []
			for name in App.gConfigFile.getSections():
				cfg = CfgSectionWrapper(App.gConfigFile, name)
				out.append(Data_ConfigSection(name=cfg.getName(),
				  remote_accepted=False,
				  pwd=cfg.getPassword()))
			App.gSlaveClient.sendConfigListReply(message, out)
		elif message.msg_type == MessageType.MASTER_REQUEST_STATISTIC:
			out = getStatistic()
			App.gSlaveClient.sendStatisticReply(message, out)
		elif message.msg_type == MessageType.MASTER_REQUEST_SHOW_MESSAGE:
			setStatus(message.msg_payload)
		elif message.msg_type == MessageType.MASTER_REQUEST_SLAVE_SHUTDOWN:
			if message.msg_payload in App.gSlaveClient.getName():
				App.gExit = True
				App.pwdButton.click()

	def onConfigReply(message: Data_ConfigSection):
		updateConfig(message)
		checkConfig(message)

	def onConfigRequest(cfgName):
		setStatus(getString(Strings.STR_ACCESS_REQUEST) + App.nextElipces())

	App.gSlaveClient = SlaveClient()
	App.gSlaveClient.start(onMasterRequest)
	App.gSlaveClient.startConfigRequestLoop(App.gGameConfig.getName(), onConfigReply, onConfigRequest, 10)

def main():
	_, *params = sys.argv

	if len(params) == 0:
		params.append("uncom")

	if len(params) == 0:
		exit()

	SYS_VAR = os.environ.get('GAME_WRAPPER_CONFIG_FILE')
	if SYS_VAR:
		App.CONFIG_FILE_PATH = SYS_VAR

	SYS_VAR = os.environ.get('USERNAME')
	if SYS_VAR:
		App.gUserName = SYS_VAR
	
	print(f'Current user: {App.gUserName}')

	App.gGameConfigName = params[0]
	App.gConfigFile = ConfigFile.read(App.CONFIG_FILE_PATH)
	App.gGameConfig = CfgSectionWrapper(App.gConfigFile, App.gGameConfigName)

	layout = [
		[sg.Text(getString(Strings.STR_ENTER_PWD))], 
		[sg.Text(getString(Strings.STR_PASSWORD), justification='right'), App.pwdInput,],
		[sg.Text(text=getString(Strings.STR_TIME), justification='right'), App.timeInput,],
		[sg.Text(getString(Strings.STR_STATUS), justification='right'), App.statusLine,],
		[App.pwdButton]
	]

	# Create the window
	App.window = sg.Window(f"Game launcher 1.0 - {App.gGameConfig.getName()}", layout)

	threading.Timer(1, doAppLoop).start()

	# Create an event loop
	while App.gExit == False:
		event, values = App.window.read()
		try:
			if App.gExit:
				if App.gStopThread:
					App.gStopThread.cancel()
				break
			# End program if user closes window or
			# presses the OK button
			if event == "pwdButtonId":
				pwd = values['pwdInputId']
				timelimit = values['timeInputId']
				App.gTimeLimit = 0
				if len(timelimit):
					App.gTimeLimit = int(timelimit)
				launchGameFromPassword(pwd)
				if App.gExit:
					break
			elif event == sg.WIN_CLOSED:
				App.gExit = True
				if App.gStopThread:
					App.gStopThread.cancel()
				break
		except:
			pass

	App.gSlaveClient.sendLogMessageRequest(f'Slave shutdown')
	App.gSlaveClient.stop()
	App.window.close()


if __name__ == "__main__": 
    main()