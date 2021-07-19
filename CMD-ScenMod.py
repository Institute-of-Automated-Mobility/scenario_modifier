#Program Info
#Version: Command Line
#Author: Shujauddin Rahimi
#Last Edited: 7/19/21

import xml.etree.ElementTree as ET
import itertools
import os
import json
import shutil
import copy
from pathlib import Path
from datetime import datetime
import sys

#Global Variables
scen_loaded = 0
scen_name = ""

config_loaded = 0
config_name = ""

debug_flag = 0

ego_speed = 0
other_speed = 0
relative_distance_to_ego = 0

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

def CheckArgs():
    if len(sys.argv) < 3 or len(sys.argv) > 3:
        print("ERROR: Incorrect number of arguments. Please format like so: python CMD-ScenMod.py <scenario_template_file>.xosc <configuration_file>.json")
        return -1
    else:
        return 0

def OpenXOSC(file_name):
    print("FUNCTION: OpenXOSC(), opening .xosc file.")

    try:
        scen_file = open(file_name)
    except FileNotFoundError:
        print("ERROR: Scenario template file {} not found.".format(file_name))
        return -1

    global scen_name
    scen_name = file_name

    if scen_file:
        ParseXOSC(file_name)

def ParseXOSC(file_name):
    print("FUNCTION: ParseXOSC(), parsing .xosc file.")

    XOSC_tree = ET.parse(file_name)
    XOSC_root = XOSC_tree.getroot()

    for parameter in XOSC_root.iter('ParameterDeclaration'):

        name = parameter.get("name")
        value = parameter.get("value")

        #Used for naming of generated files
        if name == "ego_speed":
            ego_speed = (int(float(value)))
        elif name == "other_speed":
            other_speed = (int(float(value)))
        elif name == "relative_distance_to_ego":
            relative_distance_to_ego = (int(float(value)))

        #Adding imported parameters to the imported_param_list.
        if (value[0].isnumeric()):
            imported_param = Parameter(name, value, "SET", 1)
            imported_param_list.append(imported_param)
        else:
            imported_param = Parameter(name, value, "TEXT", 1)
            imported_param_list.append(imported_param)

def OpenConfig(file_name):
    print("FUNCTION: OpenConfig(), opening .json file.")

    config_file = file_name

    global config_name
    config_name = file_name

    if config_file:
        return_val = ParseConfig(file_name)

        if return_val == -1:
            return -1

def ParseConfig(file_name):
    if os.path.isfile(file_name) == False:
        print("ERROR: Configuration file {} not found.".format(file_name))
        return -1

    file = open(file_name)



    data = json.load(file)

    print_max_width = 0

    print("FUNCTION: ParseConfig(), parsing .json file.")

    base_file_name = Path(scen_name).stem

    #Parse through the larger blocks of the .json
    for item in data:
        #Select the block that contains the same name as the scenario file
        if base_file_name.lower() == item.lower():
            for key, value in data[item].items():

                #If the type is int or float, add to the mod_param_list with type "SET"
                if type(value[0]) == int or type(value[0]) == float:
                    value = [float(x) for x in value]

                    mod_param = Parameter(key, value, "SET", len(value))

                    mod_param_list.append(mod_param)

                #If the type is string, add to the mod_param_list with type "TEXT"
                else:
                    mod_param = Parameter(key, value, "TEXT", len(value))

                    mod_param_list.append(mod_param)

    CalculateNumOfFiles(mod_param_list)

    print("LIST: mod_param_list")
    PrintList(mod_param_list)


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
def GenerateFiles():
    print("FUNCTION: GenerateFiles(), generating files.")

    if not mod_param_list:
        print("ERROR: mod_param_list is empty.")
        return 0

    combination_list = []
    intermediary_list = []
    final_list = []
    batch_number = 0
    list_of_controllers = []

    #First, the input list is flattened
    flat_param_list = FlattenList(mod_param_list)

    curr_index = 0
    #Used to make the ego_controller the first variable in the Cartesian product, allowing the files to be sorted by ego_controller when generated
    for item in flat_param_list:
        if item.name == "ego_controller":
            temp_item = copy.deepcopy(flat_param_list[0])
            flat_param_list[0] = item
            flat_param_list[curr_index] = temp_item
        curr_index = curr_index + 1

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
#    if debug_flag == 1:
#        print("final_list")
#        for item in final_list:
#            print(item)

    base_file_name = Path(scen_name).stem
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

    #Creates folders for the list of controllers
    for item in list_of_controllers:
        controller_path = os.path.join(inner_path, item)
        os.mkdir(controller_path)

    #For debugging purposes
    #print("Base path: {}\nFolder name: {}\n Directory created: {}\n".format(base_path, folder_name, path))

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

        shutil.copy(scen_name, temp_path)

        tree = ET.parse(temp_path)
        root = tree.getroot()

        i = i + 1

        #Variables used for the naming construct
        les = int(ego_speed)
        los = int(other_speed)
        lrdte = int(relative_distance_to_ego)

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

    print("NOTICE: Files successfully generated!")


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

#Calculates the number of files to be generated and returns it.
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

    return total_files

    #temp_file_string = "Total files to be generated: {total}".format(total = int(total_files))
    #files_msg.set(temp_file_string)


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

#Used to get the controllers that are in the list
def GetControllers(param_list):
    for item in param_list:
        if item.name == "ego_controller":
            return item.value

    return -1


if __name__ == "__main__":
    if CheckArgs() != -1:
        if OpenXOSC(sys.argv[1]) == -1:
            sys.exit()

        if OpenConfig(sys.argv[2]) == -1:
            sys.exit()

        print("Number of files to be generated: {}\n".format(CalculateNumOfFiles(mod_param_list)))

        exit_flag = 0

        while exit_flag == 0:
            val = input("Would you like to continue? (y/n): ")
            if val.lower() == "y":
                GenerateFiles()
                exit_flag = 1
            elif val.lower() == "n":
                print("Exiting program.")
                sys.exit()
            else:
                print("ERROR: Invalid input. Please enter 'y' or 'n'.")
