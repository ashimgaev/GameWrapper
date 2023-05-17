import PySimpleGUI as sg
import os
import sys
import subprocess
from slave import SlaveClient
from config_file import ConfigFile, ConfigSchema
from data import *
import re
import threading



class App:
	# Path to config file
	#CONFIG_FILE_PATH = "C:\Games\game_wrapper\config.ini"
	CONFIG_FILE_PATH = "slave_config.ini"

	# Section to find in config. Came from start params
	gGameCfgSection = "DEFAULT"

	# Build config
	gConfigFile = None

	gSuperUserMode = False

	gSlaveClient = None

	gExit = False

	gGameStarted = False

	gTimeLimit = 0

	gStopThread: threading.Timer

	window: sg.Window
	pwdButton = sg.Button("OK", key='pwdButtonId')
	pwdInput = sg.InputText(size=(65, 1), password_char='*', key='pwdInputId')
	timeInput = sg.InputText(size=(65, 1), key='timeInputId')
	statusLine = sg.InputText(size=(65, 1), key='statusInputId')

def setStatus(msg: str):
	print(f'Status: {msg}')
	#App.statusLine.update(value=str)

def onSuperUserMode():
	App.gSuperUserMode = True
	App.gSlaveClient.stop()

def onGameTimeout():
	print('GAME timeout!!!')
	stopGame()

def stopGame():
	setStatus('BLOCKED')
	with subprocess.Popen(f"tasklist", stdout=subprocess.PIPE, shell=True, text=True, encoding='UTF-8') as proc:
		str, _ = proc.communicate()
		proc_name = App.gConfigFile.getParam(App.gGameCfgSection, ConfigSchema.PARAM_NAME_PROC_NAME)
		for line in str.splitlines():
			if proc_name in line:
				proc_id = re.findall('[0-9]+', line)[0]
				print(f"kill {proc_id}")
				os.kill(int(proc_id), 9)
	if App.gGameStarted:
		App.gExit = True
		App.pwdButton.click()

def startGame():
	gamePath = App.gConfigFile.getParam(App.gGameCfgSection, ConfigSchema.PARAM_NAME_EXEC_PATH)
	if gamePath and App.gGameStarted == False:
		print('Start game!!!')
		App.gGameStarted = True
		os.startfile(gamePath)
		App.gSlaveClient.setConfigLoopPeriod(60)

def updateConfig(cfg_section: Data_ConfigSection):
	currPwd = App.gConfigFile.getParam(cfg_section.name, ConfigSchema.PARAM_NAME_PASSWORD)
	if currPwd != cfg_section.pwd:
		App.gConfigFile.setParam(cfg_section.name, ConfigSchema.PARAM_NAME_PASSWORD, cfg_section.pwd)
		App.gConfigFile.write()

def checkConfig(cfg_section: Data_ConfigSection):
	if not App.gSuperUserMode and App.gGameCfgSection == cfg_section.name:
		if cfg_section.remote_accepted == False:
			stopGame()
		else:
			startGame()

def startStopTimer(timeoutSec: int):
	print(f'Start GAME timeout {timeoutSec} sec!!!')
	App.gStopThread = threading.Timer(timeoutSec, onGameTimeout)
	App.gStopThread.start()

def checkPassword(input_pwd: str):
	superuser_pwd = App.gConfigFile.getParam(ConfigSchema.SECTION_NAME_SUPERUSER, ConfigSchema.PARAM_NAME_PASSWORD)
	if superuser_pwd and input_pwd == superuser_pwd:
		return (True, True)
	config_pwd = App.gConfigFile.getParam(App.gGameCfgSection, ConfigSchema.PARAM_NAME_PASSWORD)
	if config_pwd:
		return (config_pwd == input_pwd, False)
	return (False, False)

def launchGame(pwd: str):
	goodPwdFlag, superUserFlag = checkPassword(pwd)
	
	if superUserFlag:
		onSuperUserMode()
	
	if goodPwdFlag or superUserFlag:
		startGame()
		timeLimit = App.timeInput.get()
		if len(timeLimit) > 0:
			startStopTimer(int(timeLimit)*60)
	else:
		setStatus('Wrong password')
		print('Wrong password!!!')

layout = [
	[sg.Text("Please enter password")], 
	[sg.Text('Password:', justification='right'), App.pwdInput,],
	[sg.Text(text='Time:', justification='right'), App.timeInput,],
	[App.pwdButton]
	]

def main():
	_, *params = sys.argv

	if len(params) == 0:
		params.append("uncom")

	if len(params) == 0:
		exit()

	CONFIG_VARIABLE = os.environ.get('GAME_WRAPPER_CONFIG_FILE')
	if CONFIG_VARIABLE:
		App.CONFIG_FILE_PATH = CONFIG_VARIABLE

	App.gConfigFile = ConfigFile.read(App.CONFIG_FILE_PATH)

	App.gGameCfgSection = params[0]

	# Create the window
	App.window = sg.Window("Game launcher 1.0", layout)

	def onMasterRequest(message):
		print(f'master request: {str(message)}')
		if message.msg_type == MessageType.MASTER_REQUEST_CONFIG_UPDATE:
			updateConfig(message.cfg_section)
			checkConfig(message.cfg_section)

	def onConfigReply(message: Data_ConfigSection):
		updateConfig(message)
		checkConfig(message)

	def onConfigRequest(cfgName):
		setStatus(f'Requesting config [{cfgName}]')

	App.gSlaveClient = SlaveClient()
	App.gSlaveClient.start(onMasterRequest)
	App.gSlaveClient.startConfigRequestLoop(App.gGameCfgSection, onConfigReply, onConfigRequest, 10)

	setStatus('Requesting for remote access...')

	# Create an event loop
	while True:
		event, values = App.window.read()
		try:
			if App.gExit:
				break
			# End program if user closes window or
			# presses the OK button
			if event == "pwdButtonId":
				pwd = values['pwdInputId']
				timelimit = values['timeInputId']
				App.gTimeLimit = 0
				if len(timelimit):
					App.gTimeLimit = int(timelimit)
				launchGame(pwd)
				if App.gExit:
					break
			elif event == sg.WIN_CLOSED:
				break
		except:
			pass

	App.gSlaveClient.stop()
	App.window.close()


if __name__ == "__main__": 
    main()