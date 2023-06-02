from valclient.client import Client
from datetime import datetime
import json
import PySimpleGUI as sg
import os
import time
import threading
import requests

#add rightclick menu(delete, load, rename) and double click to load

mon = {'top': 140, 'left': 1400, 'width': 470, 'height': 150}

client = Client(region="eu")
client.activate()

right_click_menu = ["", ["Load", "Delete"]]

layout = [
	[
		[
			sg.In(size=(15, 1), enable_events=True, key="-LOADOUTNAME-", default_text="Loadout Name"),
			sg.Button("Save Loadout", key="-SAVE-"),
			sg.Text(key="-SAVETEXT-")
		],
		[
			sg.Listbox(
				values=[], right_click_menu=right_click_menu, enable_events=True, size=(40, 20), expand_y=True, key="-FILE LIST-"
			)
		],
		[sg.Text("Choose a loadout from the list or activate Auto Load.")],
		[
			sg.Button("Load Loadout", key="-LOAD-"),
			sg.Text(key="-LOADTEXT-")
		],
		[
			sg.Checkbox("Auto Load", default=False, key="-AL-", enable_events=True),
			sg.Text(key="-DEBUG-")
		],
		[sg.Button(key="-INIT-", visible=False)]
	]
]

window = sg.Window("Loadouts", layout, finalize=True)

def lower_and_replace_illegal_chars(text):
	return text.lower().replace("/", "").replace("\\", "").replace(":", "").replace("*", "").replace("?", "").replace('"', "").replace("<", "").replace(">", "").replace("|", "")

def save_loadout(name):
	loadout = client.fetch_player_loadout()

	name = lower_and_replace_illegal_chars(name)

	print(name)

	config_loadout = {
		"name": name,
		"created_on": datetime.today().strftime("%d-%m-%Y %H:%M"),
		"loadout": loadout
	}

	json_object = json.dumps(config_loadout, indent=2)
	file_name = "loadouts" + "/" + name + ".json"

	if os.path.exists(file_name):
		window["-SAVETEXT-"].update("Overwritten " + name + ".")
	else:
		window["-SAVETEXT-"].update("Saved " + name + ".")

	with open(file_name, "w") as outfile:
		outfile.write(json_object)

def load_loadout(name):
	try:
		with open("loadouts"+"/"+name+".json", "r") as openfile:
			json_object = json.load(openfile)
			client.put_player_loadout(json_object["loadout"])
			window["-LOADTEXT-"].update("Loaded " + name + ".")
	except:
		pass

def loud_default_folder():
	folder = "loadouts/"
	os.makedirs(os.path.dirname(folder), exist_ok=True)

	try:
		file_list = os.listdir(folder)
	except:
		file_list = []

	fnames = [
		f.replace(".json", "")
		for f in file_list
		if os.path.isfile(os.path.join(folder, f))
		and f.lower().endswith((".json"))
	]

	window["-FILE LIST-"].update(fnames)

def get_updated_list():
	folder = "loadouts/"

	try:
		file_list = os.listdir(folder)
	except:
		file_list = []

	fnames = [
		f.replace(".json", "")
		for f in file_list
		if os.path.isfile(os.path.join(folder, f))
		and f.lower().endswith((".json"))
	]

	return fnames

def is_in_pregame():
	try:
		x = client.pregame_fetch_match()
		if x != "":
			return True
	except:
		return False
	
def get_agent_name(puuid):
	url = "https://valorant-api.com/v1/agents/"+puuid

	try:
		response = requests.get(url)
		json_response = json.loads(response.text)

		return json_response["data"]["displayName"]
	except:
		pass

do_run = False
def clock():
	window["-DEBUG-"].update("Clock started.")
	while do_run == True:
		window["-DEBUG-"].update("Not in pregame.")
		while is_in_pregame() == True:
			window["-DEBUG-"].update("Pregame detected. Lock an agent.")

			all_loadouts = get_updated_list()

			try:
				pregame_match_players = client.pregame_fetch_match()["AllyTeam"]["Players"]
				pregame_player = client.pregame_fetch_player()["Subject"]

				for player in pregame_match_players:
					if player["Subject"] == pregame_player and player["CharacterSelectionState"] == "locked":
						current_agent = get_agent_name(player["CharacterID"])
						current_agent = lower_and_replace_illegal_chars(current_agent)

						if current_agent in all_loadouts:
							load_loadout(current_agent)
							break
			except:
				pass
			
	time.sleep(1)

window["-INIT-"].click()

while True:	
	#GUI
	event, values = window.read()

	if event == "-INIT-":
		loud_default_folder()

		fnames = get_updated_list()
		window["-FILE LIST-"].update(fnames)

	if event == "-FILE LIST-":
		try:
			filename = os.path.join(
				"loadouts", values["-FILE LIST-"][0]
			)
		except:
			pass

	if event == "-SAVE-":
		try:
			if values["-LOADOUTNAME-"] != "":
				save_loadout(values["-LOADOUTNAME-"])
				fnames = get_updated_list()
				window["-FILE LIST-"].update(fnames)
		except:
			pass

	if event == "-LOAD-":
		load_loadout(values["-FILE LIST-"][0])

	if event == "-AL-":
		thread = threading.Thread(target=clock)

		if values["-AL-"] == True:
			thread.start()
			do_run = True
			window["-DEBUG-"].update("Activated Auto Load.")
		else:
			do_run = False
			window["-DEBUG-"].update("Deactivated Auto Load.")

	if event == "Exit" or event == sg.WIN_CLOSED:
		break

	#Right Click Menu
	if event == "Delete":
		if len(values["-FILE LIST-"]) != 0:
			os.remove("loadouts" + "/" + values["-FILE LIST-"][0] + ".json")
			
			fnames = get_updated_list()
			window["-FILE LIST-"].update(fnames)

	if event == "Rename":
		if len(values["-FILE LIST-"]) != 0:
			current_loadout = values["-FILE LIST-"][0]

	if event == "Load":
		if len(values["-FILE LIST-"]) != 0:
			load_loadout(values["-FILE LIST-"][0])

do_run = False
window.close()