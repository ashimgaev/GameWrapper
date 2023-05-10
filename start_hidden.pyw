import PySimpleGUI as sg
import os
import configparser
import sys


# Path to config file
CONFIG_FILE_PATH = "C:\Games\game_wrapper\config.ini"

# Config file schema
PARAM_NAME_PASSWORD = "password"
PARAM_NAME_EXEC_PATH = "exec_path"

# Section to find in config. Came from start params
GAME_CFG_SECTION = "DEFAULT"

def checkPassword(pwd: str):
	if GAME_CFG_SECTION in config.sections():
		return pwd == config[GAME_CFG_SECTION][PARAM_NAME_PASSWORD]
	return False

def launchGame(pwd: str):
	if checkPassword(pwd):
		print('Start game!!!')
		gamePath = config[GAME_CFG_SECTION][PARAM_NAME_EXEC_PATH]
		os.startfile(gamePath)
	else:
		print('Wrong password!!!')

pwdButton = sg.Button("OK", key='pwdButtonId')
pwdInput = sg.InputText(size=(65, 1), password_char='*', key='pwdInputId')
layout = [
	[sg.Text("Please enter password")], 
	[sg.Text('Password:', justification='right'), pwdInput,],
	[pwdButton]
	]

# Build config
config = configparser.ConfigParser()

def main():
	_, *params = sys.argv

	#params = []
	#params.append("cossaks")

	if len(params) == 0:
		exit()

	with open(CONFIG_FILE_PATH, encoding='utf-8') as cfgFile:
		config.readfp(cfgFile)

	global GAME_CFG_SECTION 
	GAME_CFG_SECTION = params[0]

	# Create the window
	window = sg.Window("Game launcher 1.0", layout)

	# Create an event loop
	while True:
		event, values = window.read()
		# End program if user closes window or
		# presses the OK button
		if event == "pwdButtonId":
			launchGame(values['pwdInputId'])
			#break
		elif event == sg.WIN_CLOSED:
			break

	window.close()


if __name__ == "__main__": 
    main()