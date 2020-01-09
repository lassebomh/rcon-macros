import valve.rcon
from tkinter import *
from tkinter.ttk import *
from functools import partial
from difflib import SequenceMatcher
from operator import itemgetter
from PIL import ImageTk, Image
import os

root = Tk()
root.title("CS-Control")
root.resizable(0, 0)
host = ()
password = ""
commands = {}
buttons = []
datapath = os.path.dirname(os.path.realpath(__file__))+"\\assets\\"

def updateSettings():
	open(datapath+"cs-control.data", 'a').close()
	userdata = open(datapath+"cs-control.data", 'r').read()
	if userdata == "":
		open(datapath+"cs-control.data", 'w').write('ip 1.1.1.1\nhost 27015\npassword 123456\n{\n}')

	with open(datapath+"cs-control.data", 'r') as rcondata:
		global host, password, commands
		rcon = rcondata.read()
		host = eval("(\'"+rcon.split("\n")[0][3:]+"\', "+rcon.split("\n")[1][5:]+")")
		password = rcon.split("\n")[2][9:]
		commands = eval("".join(rcon.split("\n")[3:]))

def runCommand(button):
	with valve.rcon.RCON(host, password) as rcon:
		rcon.execute(commands[button])

def runCommand1(a=""):
	with valve.rcon.RCON(host, password) as rcon:
		rcon.execute(commandEntry.get())

maps = []

def scanMapsLoop(a=""):
	global maps
	try:
		with valve.rcon.RCON(host, password) as rcon:
			raw_map_list = rcon.execute("maps *")
	except: pass
	try:
		maps = raw_map_list.text.replace("-------------\n", "").replace("PENDING:   (fs) ", "").replace(".bsp", "").split("\n")
		root.after(5000, scanMapsLoop)
	except:
		pass

def scanMaps(a=""):
	global maps
	maplist_box.delete(0, END)
	listen = {x:int(SequenceMatcher(None, x, maplist_entry.get()).ratio()*1000) for x in maps}
	for obj in filter(lambda x: x!="" and x[0]!="L", sorted(listen, key=listen.__getitem__, reverse=True)):
		maplist_box.insert(END, obj)

def loadMap(a=""):
	maplist_entry.delete(0, END)
	maplist_entry.insert(END, maplist_box.get(0))
	root.update()
	with valve.rcon.RCON(host, password) as rcon:
		rcon.execute("map "+maplist_entry.get())

def settings():
	updateSettings()
	global commands, drumpImage
	tempCommand = commands

	def removeCommand(a=""):
		del commands[commandsListbox.get(ACTIVE)]
		updateListbox()
		updateText()

	def addCommand():
		if newEntry.get().replace(" ", "") != "":
			commands[newEntry.get()] = ''
			updateListbox()
			updateText()

	def updateListbox():
		commandsListbox.delete(0, END)
		for x in commands.keys():
			commandsListbox.insert(END, x)

	def updateText(a=""):
		scriptText.delete('1.0', END)
		scriptText.insert(END, commands[commandsListbox.get(ACTIVE)].replace("; ","\n"))

	def cancel():
		settingsRoot.destroy()

	def accept():
		global buttons
		host = (ipEntry.get(), portEntry.get())
		password = rconpasswordEntry.get()
		commands = tempCommand
		with open(datapath+"cs-control.data", 'w') as userdata:
			userdata.write("ip "+host[0]+"\nhost "+str(host[1])+"\npassword "+password+"\n{\n"+str(commands).replace(", ", ",\n")[1:-1]+"\n}")
		for x in buttons:
			x.destroy()
			del x
		for y, x in enumerate(commands.keys()):
			buttons.append(Button(custombuttonFrame, text=x, command=partial(runCommand, x), width=25))
			buttons[-1].pack(padx=2, pady=2)
		cancel()

	def saveTrigger(a=""):
		settingsRoot.after(120, save)
	
	def save():
		tempCommand[commandsListbox.get(ACTIVE)] = scriptText.get('1.0', END).replace("\n", "; ")

	def updateListboxTrigger(a=""):
		settingsRoot.after(120, updateText)

	def callback(event):
		#open_new(r"https://youtu.be/Ue4PHfMWKzA?t=16s")
		pass

	settingsRoot = Toplevel(root)
	settingsRoot.title("Settings")
	settingsRoot.resizable(0, 0)

	drumpFrame = Label(settingsRoot)
	drumpFrame.pack(padx=5, pady=4)
	loginFrame = LabelFrame(drumpFrame, text="Login")
	loginFrame.pack(ipadx=4, ipady=4, side=LEFT, padx=(0, 10))
	drumpImage = ImageTk.PhotoImage(Image.open(datapath+"53.png").resize((120, 65), Image.ANTIALIAS))
	drumpLabel = Label(drumpFrame, image=drumpImage)
	drumpLabel.pack(side=LEFT, pady=(7, 0))
	drumpLabel.bind("<Button-1>", callback)
	topFrame = Frame(loginFrame)
	topFrame.pack()
	ipFrame = Frame(topFrame)
	ipFrame.pack(side=LEFT)
	Label(ipFrame, text="IP: ").pack(side=LEFT)
	ipEntry = Entry(ipFrame, width=16)
	ipEntry.insert(END, host[0])
	ipEntry.pack(side=LEFT)
	portFrame = Frame(topFrame)
	portFrame.pack(side=LEFT, padx=2)
	Label(portFrame, text="Port: ").pack(side=LEFT)
	portEntry = Entry(portFrame, width=7)
	try: portEntry.insert(END, host[1])
	except: pass
	portEntry.pack(side=LEFT)
	rconFrame = Frame(loginFrame)
	rconFrame.pack(pady=(5, 0))
	Label(rconFrame, text="RCON Password: ").pack(side=LEFT)
	rconpasswordEntry = Entry(rconFrame, width=17)
	rconpasswordEntry.insert(END, password)
	rconpasswordEntry.pack(side=LEFT)

	managemainFrame = LabelFrame(settingsRoot, text="Manage macros")
	managemainFrame.pack(ipadx=4, ipady=4, padx=6, pady=1)
	manageFrame = Frame(managemainFrame)
	manageFrame.pack(side=LEFT)
	addFrame = Frame(manageFrame)
	addFrame.pack(padx=4, pady=(0, 4))
	newEntry = Entry(addFrame, width=16)
	newEntry.pack(side=LEFT)
	addButton = Button(addFrame, text="Add", width=5, command=addCommand)
	addButton.pack(side=LEFT, padx=4)
	commandsListbox = Listbox(manageFrame, height=12, width=25)
	commandsListbox.pack()
	commandsListbox.bind("<<ListboxSelect>>", updateListboxTrigger)
	commandsListbox.bind("<Delete>", removeCommand)
	updateListbox()
	deleteButton = Button(manageFrame, text="Delete macro", command=removeCommand, width=24)
	deleteButton.pack(padx=4, pady=(0, 4))
	scriptText = Text(managemainFrame, width=30, height=19, font=('Consolas', 8))
	scriptText.pack(side=LEFT)
	scriptText.bind("<Key>", saveTrigger)
	buttonsFrame = Frame(settingsRoot)
	buttonsFrame.pack(pady=7)
	acceptButton = Button(buttonsFrame, text="Accept", command=accept, width=10)
	acceptButton.pack(side=LEFT, padx=(215, 4))
	cancelButton = Button(buttonsFrame, text="Cancel", command=cancel, width=10)
	cancelButton.pack(side=LEFT, padx=0)

titleFrame = Frame(root)
titleFrame.pack(pady=(5, 0))
yesImage = ImageTk.PhotoImage(Image.open(datapath+"yes.png").resize((90, 18), Image.ANTIALIAS))
yesLabel = Label(titleFrame, image=yesImage)
yesLabel.pack(side=LEFT, padx=(0, 2))
settingsImage = PhotoImage(file=datapath+"settings.png")
settingsButton = Button(titleFrame, image=settingsImage, command=settings, width=9)
settingsButton.pack(side=LEFT, padx=4)
helpImage = PhotoImage(file=datapath+"help.png")
helpButton = Button(titleFrame, image=helpImage, command=settings, width=9)
helpButton.pack(side=LEFT)

maincustombuttonFrame = Frame(root)
maincustombuttonFrame.pack()
custombuttonFrame = LabelFrame(maincustombuttonFrame, text="Macros")
custombuttonFrame.pack(ipadx=3, ipady=3, padx=5)
updateSettings()
for y, x in enumerate(commands.keys()):
	buttons.append(Button(custombuttonFrame, text=x, command=partial(runCommand, x), width=25))
	buttons[-1].pack(padx=2, pady=2)
commandMainFrame = LabelFrame(root, text="Run command")
commandMainFrame.pack(ipadx=5, ipady=3, pady=5)
commandFrame = Frame(commandMainFrame)
commandFrame.pack()
commandEntry = Entry(commandFrame, width=18)
commandEntry.pack(side=LEFT, padx=(0,6))
commandEntry.bind("<Return>", runCommand1)
setcommandButton = Button(commandFrame, width=5, text="Run", command=runCommand1)
setcommandButton.pack(side=LEFT)

mapFinderFrame = LabelFrame(root, text="Maps")
mapFinderFrame.pack(ipadx=5, ipady=3, pady=(0,5))
mapEntryFrame = Frame(mapFinderFrame)
mapEntryFrame.pack()

def updateEntry(a=""):
	maplist_entry.delete("0", END)
	maplist_entry.insert(END, maplist_box.get(ACTIVE))

def scanMapsDelay(a=""):
	root.after(120, scanMaps)

maplist_entry = Entry(mapEntryFrame, width=17)
maplist_entry.pack(side=LEFT)
maplist_entry.bind("<Key>", scanMapsDelay)
maplist_entry.bind("<Return>", loadMap)
mapload_button = Button(mapEntryFrame, text='Load', command=loadMap, width=6)
mapload_button.pack(side=LEFT, padx=(6, 0))
maplist_box = Listbox(mapFinderFrame, width=26, height=4)
maplist_box.pack(padx=(0, 2), pady=(4, 0))
maplist_box.bind("<<ListboxSelect>>", (lambda A="": root.after(120, updateEntry)))

# scanMapsDelay()
# root.after(1, scanMapsLoop)
mainloop()
