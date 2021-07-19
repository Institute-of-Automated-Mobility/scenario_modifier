#Program Info
#Version: GUI
#Author: Shujauddin Rahimi
#Last Edited: 7/19/21

import tkinter as tk
from tkinter import ttk
from tkinter import *
import xml.etree.ElementTree as ET
from tkinter.filedialog import askopenfile
import itertools
import os
import json
import shutil
import copy
from pathlib import Path
from datetime import datetime

root = tk.Tk()
root.title("Scenario Modifier")
root.minsize(830, 330)

canvas = tk.Canvas(root, width = 830, height = 330)

scen_loaded = tk.IntVar()
scen_loaded.set(0)

scen_name = tk.StringVar()

config_loaded = tk.IntVar()
config_loaded.set(0)

config_name = tk.StringVar()

debug_flag = 0

ego_speed = tk.IntVar()
other_speed = tk.IntVar()
relative_distance_to_ego = tk.IntVar()

ego_speed.set(0)
other_speed.set(0)
relative_distance_to_ego.set(0)

rb_type_select = tk.IntVar()

#Imported Last Selected Parameter
imported_LSP = tk.IntVar()

modified_LSP = tk.IntVar()

imported_param_list = []
mod_param_list = []


class Parameter:
    def __init__(self, name, value, type, steps):
        self.name = name
        self.value = value
        self.type = type    #Type can be either "SET" or "TEXT"
        self.steps = steps

    def toString(self):
        return "{}: {}".format(self.name, self.value)

#Functions
#OpenXOSC() serves as the response to pressing the "Choose Scenario Template" button
def OpenXOSC():
    print("FUNCTION: OpenXOSC()")

    scen_file = askopenfile(parent = root, mode = 'rb', title = "Choose a scenario file", filetype = [("Xosc file", "*.xosc")])

    #Scenario File has been successfully loaded.
    if scen_file:
        #Refresh imported_param_list and imported_lb if a previous file was loaded.
        if scen_loaded.get() == 1:
            imported_param_list.clear()
            imported_lb.delete('0', 'end')

        board_msg.set("Scenario file")

        board_msg.set("Scenario file successfully loaded!")
        board_lbl.config(foreground = "black")
        scen_loaded.set(1)

        scen_name.set(scen_file.name)


        print("NOTICE: " + scen_name.get() + " was successfully loaded!")

        ParseXOSC(scen_name.get())

        print("\nLIST: imported_param_list")
        PrintList(imported_param_list)

        imported_lb.select_set(0)
        imported_lb.event_generate("<<ListboxSelect>>")

    else:
        #Scenario file has not been successfully loaded.

        print("ERROR: Scenario file was not loaded.")

        board_msg.set("ERROR: Scenario file was not loaded.")
        board_lbl.config(foreground = "red")


#ParseXOSC takes the xosc file and grabs the data
def ParseXOSC(file_name):
    print("NOTICE: Parsing .xosc file.")

    XOSC_tree = ET.parse(file_name)
    XOSC_root = XOSC_tree.getroot()

    #Iterate through the parameters and add them to the imported_param_list
    for parameter in XOSC_root.iter('ParameterDeclaration'):

        name = parameter.get("name")
        value = parameter.get("value")

        #Used for naming of generated files
        if name == "ego_speed":
            ego_speed.set(int(float(value)))
        elif name == "other_speed":
            other_speed.set(int(float(value)))
        elif name == "relative_distance_to_ego":
            relative_distance_to_ego.set(int(float(value)))

        #Adding imported parameters to the imported_param_list.
        if (value[0].isnumeric()):
            imported_param = Parameter(name, value, "SET", 1)
            imported_param_list.append(imported_param)
        else:
            imported_param = Parameter(name, value, "TEXT", 1)
            imported_param_list.append(imported_param)

        PostToListBox(imported_param, imported_lb, "Imported", "Add")

#OpenXOSC() serves as the response to pressing the "Choose Config File" button
def OpenConfig():
        print("FUNCTION: OpenConfig()")

        config_file = askopenfile(parent = root, mode = 'r', title = "Choose a config file", filetype = [("JSON file", "*.json")])

        #config_file successfully loaded.
        if config_file:
            print("NOTICE: Config file successfully loaded!")

            config_name.set(config_file.name)
            config_loaded.set(1)

            ParseConfig(config_name.get())
        else:
            print("ERROR: Config file was not loaded.")

            board_msg.set("ERROR: Config file was not loaded.")
            board_lbl.config(foreground = "red")
            config_loaded.set(0)

#ParseConfig takes the json file and grabs the data
def ParseConfig(file_name):
    file = open(file_name)

    data = json.load(file)

    print_max_width = 0

    print("NOTICE: Parsing config file.")

    base_file_name = Path(scen_name.get()).stem

    #Parse through the larger blocks of the .json
    for item in data:
        #Select the block that contains the same name as the scenario file
        if base_file_name.lower() == item.lower():
            for key, value in data[item].items():

                #If the type is int or float, add to the mod_param_list with type "SET"
                if type(value[0]) == int or type(value[0]) == float:
                    value = [float(x) for x in value]

                    mod_param = Parameter(key, value, "SET", len(value))
                    rb_type_select.set(2)

                    mod_param_list.append(mod_param)

                    PostToListBox(mod_param, modified_lb, "Modified", "Add")
                #If the type is string, add to the mod_param_list with type "TEXT"
                else:
                    mod_param = Parameter(key, value, "TEXT", len(value))
                    rb_type_select.set(1)

                    mod_param_list.append(mod_param)

                    PostToListBox(mod_param, modified_lb, "Modified", "Add")

    CalculateNumOfFiles(mod_param_list)

    print("\nLIST: mod_param_list")
    PrintList(mod_param_list)


#Used to determine which item in the imported_lb is selected
def ImportedLBSelect(event):
    selection = event.widget.curselection()

    if selection:
        index = selection[0]
        data = event.widget.get(index)

        imported_LSP.set(index)

        if imported_param_list[index].type == "TEXT" and not value_entry.get():
            rb_type_select.set(1)
        elif imported_param_list[index].type == "SET" and not value_entry.get():
            rb_type_select.set(2)
        elif type(value_entry.get()[0]) == int or type(value_entry.get()[0]) == float:
            rb_type_select.set(2)
        else:
            rb_type_select.set(1)


#Used to determine which item in the modified_lb is selected
def ModifiedLBSelect(event):
    selection = event.widget.curselection()

    if selection:
        index = selection[0]
        data = event.widget.get(index)

        modified_LSP.set(index)

        EditItem(index)

        #board_msg.set("To edit: modify value & 'Add Item'")


def AddItem():
    print("FUNCTION: AddItem()")

    #Reset the board message
    board_msg.set("")
    board_lbl.config(foreground = "black")

    #Scenario file has not been loaded.
    if scen_loaded.get() == 0:
        board_msg.set("ERROR: Please choose a Scenario Template first.")
        board_lbl.config(foreground = "red")
        return 0

    #if not imported_lb.get(ANCHOR):
    #    param_to_add = mod_param_list[modified_LSP.get()]

        #These two lines allow for editing items already in the mod_param_array, however there are some bugs at this time.
        #modified_lb.delete(modified_LSP.get())
        #del mod_param_list[modified_LSP.get()]
    #else:

    #param_to_add gets the item that corresponds to the selection the user has made in the imported_lb
    param_to_add = imported_param_list[imported_LSP.get()]

    #If the user has selected "Text Entry"
    if rb_type_select.get() == 1:
        value = value_entry.get().strip().split(" ")

        mod_param = Parameter(param_to_add.name, value, "TEXT", len(value))

        mod_param_list.append(mod_param)

        PostToListBox(mod_param, modified_lb, "Modified", "Add")

    #If the user has selected "Number Set"
    elif rb_type_select.get() == 2:
        try:
            raw_number_set = list(value_entry.get().strip().split(" "))
            clean_set = list(map(float, raw_number_set))

        except ValueError:
            print("ERROR: Non-number entry.")

            board_msg.set("ERROR: Please enter numbers only.")
            board_lbl.config(foreground = "red")

            return 0

        mod_param = Parameter(param_to_add.name, clean_set, "SET", len(clean_set))

        mod_param_list.append(mod_param)

        PostToListBox(mod_param, modified_lb, "Modified", "Add")

    #If the user has selected "Lower-Step-Upper"
    else:
        try:
            raw_number_set = list(value_entry.get().strip().split(" "))
            clean_set = list(map(float, raw_number_set))

        except ValueError:
            print("ERROR: Non-number entry.")

            board_msg.set("ERROR: Please enter numbers only.")
            board_lbl.config(foreground = "red")
            return 0


        if len(clean_set) > 3 or len(clean_set) < 3:
            board_msg.set("ERROR: Please enter three values.")
            board_lbl.config(foreground = "red")
            return 0

        else:
            lower = clean_set[0]
            step = clean_set[1]
            upper = clean_set[2]

            if upper <= lower:
                board_msg.set("ERROR: Upper <= lower. Please change an entry.")
                board_lbl.config(foreground = "red")
                return 0

            elif ((upper - lower) % step !=  0):
                board_msg.set("ERROR: Step does not fit. Please change an entry.")
                board_lbl.config(foreground = "red")
                return 0

            else:
                mod_param = Parameter(param_to_add.name, StepCreate(lower, step, upper), "SET", len(clean_set))

                mod_param_list.append(mod_param)

                PostToListBox(mod_param, modified_lb, "Modified", "Add")


    print("\nLIST: mod_param_list")
    PrintList(mod_param_list)


#Function that handles updating the listboxes
def PostToListBox(parameter, listbox, param_list, command):
    if command == "Add":
        listbox.insert("end", parameter.toString())
    else:
        listbox.delete(modified_LSP.get())

    CalculateNumOfFiles(mod_param_list)


#Helper function for creating stepped data entries
def StepCreate(lower, step, upper):
    output = []

    number_of_indices = (upper - lower)/step
    output.append(lower)

    for i in range(int(number_of_indices)):
        output.append(output[i] + step)

    return output


#FlattenList is used for updating the total files count when adding and removing items. It's also used in the GenerateFiles() function for creating the right combinations.
def FlattenList(input_list):
    internal_list = copy.deepcopy(input_list)

    output_list = []
    keep_track = []
    index = 0

    #Goes through all items in the list
    for item in internal_list:
        #keep_track serves to create a list without duplicates so the input list can be flattened
        if item.name not in keep_track:
            keep_track.append(item.name)

            new_param = Parameter(item.name, item.value, item.type, item.steps)

            output_list.append(new_param)
        else:
            #If the item is already on the output list, simply append the new values to that item
            for i in range(len(output_list)):
                if output_list[i].name == item.name:
                    index = i

                    for sub_value in item.value:
                        output_list[index].value.append(sub_value)
                        output_list[index].steps = output_list[index].steps + 1

    return output_list


#Generate files is the function used to create all the combinations of files
#This function works by flattening the list of modified parameters, then creating a Cartesian product of the items (like iter.combination), creating the corresponding number of .xosc files, and updating their data based on the Cartesian product.
def GenerateFiles():
    print("FUNCTION: GenerateFiles()")

    if not mod_param_list:
        print("ERROR: mod_param_list is empty.")

        board_msg.set("ERROR: No modified parameters.")
        board_lbl.config(foreground = "red")
        return 0

    combination_list = []
    intermediary_list = []
    final_list = []
    batch_number = 0
    list_of_controllers = []

    #First, the input list is flattened
    flat_param_list = FlattenList(mod_param_list)

    PrintList(flat_param_list)

    curr_index = 0

    #Used to make the ego_controller the first variable in the Cartesian product, allowing the files to be sorted by ego_controller when generated
    for item in flat_param_list:

        if item.name == "ego_controller":
            temp_item = copy.deepcopy(flat_param_list[0])
            flat_param_list[0] = item
            flat_param_list[curr_index] = temp_item

        curr_index = curr_index + 1

    PrintList(flat_param_list)

    list_of_controllers = GetControllers(flat_param_list)

    #This loop creates the combination_list that is then used to create the files
    for item in flat_param_list:
        if item.type == "SET":
            for i in range(len(item.value)):
                intermediary_list.append("{} {}".format(item.name, item.value[i]))

        if item.type == "TEXT":
            for sub_item in item.value:
                intermediary_list.append("{} {}".format(item.name, sub_item))

        combination_list.append(intermediary_list.copy())
        intermediary_list.clear()

    #The final list is a cartesian product of the combination list
    final_list = bigListCartProd(combination_list)

    #Prints the final list, but doesn't look great. Meant for debugging purposes
#   print("final_list")
#   for item in final_list:
#       print(item)

    base_file_name = Path(scen_name.get()).stem
    base_path = Path(__file__).parent.absolute()

    folder_name = getFileName(base_file_name)

    path = os.path.join(base_path, base_file_name)

    #Create a new scenario folder if one doesn't already exist
    try:
        os.mkdir(path)
    except FileExistsError:
        print("NOTE: {} directory already exists.".format(base_file_name))

    inner_path = os.path.join(path, folder_name)

    #Create a new sub folder if one doesn't already exist
    try:
        os.mkdir(inner_path)
    except FileExistsError:
        print("ERROR: Generate button pressed in rapid succession.")

    for item in list_of_controllers:
        controller_path = os.path.join(inner_path, item)
        os.mkdir(controller_path)

    #For debugging purposes
    #print("Base path: {}\nFolder name: {}\nDirectory created: {}\n".format(base_path, folder_name, path))

    inner_path_readme = os.path.join(inner_path, "0_README.txt")

    readme_txt = open(inner_path_readme, "w")

    id_counter = 0

    #Generate the files
    for item in final_list:
        itemSubList = item.split()
        batch_number = batch_number + 1

        id_counter = id_counter + 1
        temp_string = "ID-{}: \n".format(id_counter)
        readme_txt.write(temp_string)

        #This is used as the initial name for the file creation of each file
        temp_name = "{BFN}_{i}.xosc".format(BFN = base_file_name, i = i)

        temp_path = os.path.join(inner_path, temp_name)

        shutil.copy(scen_name.get(), temp_path)

        tree = ET.parse(temp_path)
        root = tree.getroot()

        i = i + 1

        #Variables used for the naming construct
        les = int(ego_speed.get())
        los = int(other_speed.get())
        lrdte = int(relative_distance_to_ego.get())


        #Manipulate the variables in each scenario file according to the final_list
        for parameter in root.iter('ParameterDeclaration'):


                if parameter.get("name") in itemSubList:
                    parameter_name = parameter.get("name")
                    parameter_value = itemSubList[itemSubList.index(parameter_name) + 1]

                    if debug_flag == 2:
                        print("Name: {}\t\t| Value: {}".format(parameter_name, parameter_value))
                        print("ego_speed: {}\t\t| other_speed: {}\t\t| ego_distance_to_travel: {}".format(les, los, lrdte))
                        print("")

                    parameter.set("value", parameter_value)

                    if parameter.get("name") == "ego_speed":
                        les = int(float(parameter.get("value")))
                    elif parameter.get("name") == "other_speed":
                        los = int(float(parameter.get("value")))
                    elif parameter.get("name") == "relative_distance_to_ego":
                        lrdte = int(float(parameter.get("value")))



        for parameter in root.iter('ParameterDeclaration'):
            txt_string = "{}: {}\n".format(parameter.get("name"), parameter.get("value"))
            readme_txt.write(txt_string)

            if parameter.get("name") == "ego_controller":
                controller_name = parameter.get("value")

        readme_txt.write("\n")

        inner_controller_path = os.path.join(inner_path, controller_name)

        #Renames the file with the correct naming construct
        new_name = "ID-{}_{BFN}_{x}_{y}_{z}.xosc".format(batch_number, BFN = base_file_name, x = les, y = los, z = lrdte)

        new_path = os.path.join(inner_controller_path, new_name)

        tree.write(temp_path)
        os.rename(temp_path, new_path)

    board_msg.set("NOTICE: Files successfully generated!")
    board_lbl.config(foreground = "black")

    print("\nNOTICE: Files successfully generated!")


#Used for unique folder name generation
def getFileName(base_file_name):
    now = datetime.now()

    dt_string = now.strftime("%b-%d-%y--(%I-%M-%S--%p)")

    string = "{STR}".format(STR = dt_string)

    return(string)


#Helper function that creates the correct cartesian product
def bigListCartProd(bigList):
    lastItem = bigList[len(bigList) - 1]
    i = 0
    while len(bigList) > 1 and bigList[len(bigList) - 1] == lastItem:
        bigList[i + 1] = cartesianProduct(bigList[i], bigList[i+1])
        i = i + 1

    return bigList[i]


#Helper function that creates the correct cartesian product
def cartesianProduct(list1, list2):
    output = []

    for item1 in list1:
        for item2 in list2:
            string = "{i1} {i2}"
            output.append(string.format(i1 = item1, i2 = item2))

    return output


#Clear the users entries
def ClearEntries():
    value_entry.delete(0, END)

    board_msg.set("")
    board_lbl.config(foreground = "black")


#Clear the modified parameters
def ClearModListLB():
    modified_lb.delete('0', 'end')
    mod_param_list.clear()


#Return the users radio button choice and change the message accordingly
def RBChoice():
    print("FUNCTION: RBChoice()")
    print("Radiobutton choice =", rb_type_select.get())

    if rb_type_select.get() == 1:
        choice_msg.set("Format: Alpha Beta Charlie (spaces between)")

    if rb_type_select.get() == 2:
        choice_msg.set("Format: 1 2 3 4 5 (spaces between)")

    if rb_type_select.get() == 3:
        choice_msg.set("Format: Lower Step Upper (ex. 10 5 20)")


#Used to display the number of files that will be generated
def CalculateNumOfFiles(input_list):
    internal_list = copy.deepcopy(input_list)

    total_files = 0

    if not internal_list:
        total_files = 0
    else:
        total_files = 1

        flat_list = FlattenList(internal_list)

        for item in flat_list:
            total_files = total_files * item.steps

    temp_file_string = "Total files to be generated: {total}".format(total = int(total_files))
    files_msg.set(temp_file_string)


#Used to print the list with proper formatting
def PrintList(input_list):
    max_len_name = 0
    max_len_value = 0

    for item in input_list:
        if len(item.name) > max_len_name:
            max_len_name = len(item.name)
        if len(str(item.value)) > max_len_value:
            max_len_value = len(str(item.value))

    for item in input_list:
        print("Name: {}| Value: {}\t| Type: {}\t| Num. of Steps: {}".format(item.name.ljust(max_len_name + 5), str(item.value).ljust(max_len_value), item.type, item.steps))

    print("")

#Used to remove items
def RemoveItem():
    del mod_param_list[modified_LSP.get()]
    PostToListBox("None", modified_lb, "Modified", "Remove")

    print("\nLIST: mod_param_list")
    PrintList(mod_param_list)


#Used to get the value of whatever the user selects in the modified_lb
def EditItem(index):
    value_entry.delete(0, END)
    value_entry.insert(0, mod_param_list[index].value)


#Used to get the controllers that are in the list
def GetControllers(param_list):
    for item in param_list:
        if item.name == "ego_controller":
            return item.value

    return -1
#--------------------------------------------------------------------------------#
#GUI elements
board_msg = tk.StringVar()
board_lbl = ttk.Label(root, textvariable = board_msg)
board_lbl.grid(column = 0, row = 0, padx = 5)


scen_btn = ttk.Button(root, text = "Choose Scenario Template", command = OpenXOSC)
scen_btn.grid(column = 0, row = 1)
scen_btn.grid(padx = 20,pady = 10, ipadx =  10)

config_btn = ttk.Button(root, text = "Choose Config File", command = OpenConfig)
config_btn.grid(column = 0, row = 2, ipadx = 30)
config_btn.grid(padx = 20,pady = 10)

generate_btn = ttk.Button(root, text = "Generate", command = GenerateFiles)
generate_btn.grid(column = 0, row = 3, ipadx = 47)
generate_btn.grid(padx = 20,pady = 10)

imported_lbl = ttk.Label(root, text = "Current parameters and values")
imported_lbl.grid(column = 1, row = 0, columnspan = 3, pady = 5)

imported_lb = tk.Listbox(root)
imported_lb.grid(column = 1, row = 1, rowspan = 3, columnspan = 3, ipadx = 80)
imported_lb.bind("<<ListboxSelect>>", ImportedLBSelect)

i_l_scrollbar = tk.Scrollbar(root, orient=HORIZONTAL)
imported_lb.config(xscrollcommand = i_l_scrollbar.set)
i_l_scrollbar.config(command = imported_lb.xview)
i_l_scrollbar.grid(column = 1, row = 4, columnspan =3, sticky = W+E, padx= 15)

custom_lbl = ttk.Label(root, text = "Value Entry")
custom_lbl.grid(column = 1, row = 5, pady = 5, columnspan = 3)

value_entry = ttk.Entry(root, width = 45)
value_entry.grid(column = 1, row = 6, columnspan = 3)

modified_lbl = ttk.Label(root, text = "Modified parameters")
modified_lbl.grid(column = 4, row = 0, columnspan = 3, pady = 5)

modified_lb = tk.Listbox(root)
modified_lb.grid(column = 4, row = 1, padx = 15, rowspan = 3, columnspan = 2, ipadx = 80)
modified_lb.bind("<<ListboxSelect>>", ModifiedLBSelect)

u_a_scrollbar = tk.Scrollbar(root, orient=HORIZONTAL)
modified_lb.config(xscrollcommand = u_a_scrollbar.set)
u_a_scrollbar.config(command = modified_lb.xview)
u_a_scrollbar.grid(column = 4, row = 4, columnspan = 2, sticky = W+E, padx= 15)

files_msg = tk.StringVar()
files_msg_lbl = ttk.Label(root, textvariable = files_msg)
files_msg_lbl.grid(column = 4, row = 5, columnspan = 3)

add_btn = ttk.Button(root, text = "Add Item", command = AddItem)
add_btn.grid(column = 4, row = 6, ipadx = 25)

remove_btn = ttk.Button(root, text = "Remove Item", command = RemoveItem)
remove_btn.grid(column = 5, row = 6, ipadx = 25)

clear_btn = ttk.Button(root, text = "Clear Entries", command = ClearEntries)
clear_btn.grid(column = 4, row = 7, ipadx = 25, pady = 5)

clear_list_btn = ttk.Button(root, text = "Clear Modified List", command = ClearModListLB)
clear_list_btn.grid(column = 5, row = 7, ipadx = 10, pady = 5)

rb_type_select = tk.IntVar()
rb_type_select.set(2)

text_choice_rb = ttk.Radiobutton(root, text = "Text Entry", variable = rb_type_select, value = 1, command = RBChoice)
text_choice_rb.grid(column = 1, row = 7, pady = 5, padx = 5)

custom_set_choice_rb = ttk.Radiobutton(root, text = "Number Set", variable = rb_type_select, value = 2, command = RBChoice)
custom_set_choice_rb.grid(column = 2, row = 7, pady = 5, padx = 5)

step_choice_rb = ttk.Radiobutton(root, text = "Lower-Step-Upper", variable = rb_type_select, value = 3, command = RBChoice)
step_choice_rb.grid(column = 3, row = 7, pady = 5, padx = 5)

choice_msg = tk.StringVar()
choice_lbl = ttk.Label(root, textvariable = choice_msg)
choice_lbl.grid(column = 1, row = 8, pady = 5, columnspan = 3)

root.mainloop()
