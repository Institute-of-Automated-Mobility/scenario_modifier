# scenario_modifier

This is a simple Python program that allows users to quickly modify a template scenario file using a .json file or a GUI. To use the program in its current state, download the code and run it from your command line.

My method of use:
1. Run program
2. Open Scenario Template File
3. Open Config File (if necessary)
4. Select the parameter in the "Current parameters and values" section
5. Enter data into "Value Entry"
6. If you select "Lower-Step-Upper" as the data form, enter your data like "1 1 10" and make sure the step is possible (for example, "1 5 7" is not possible)
7. Once you are satisfied, hit generate and a folder with the name of the template file will be generated in the location that Scenario-Modifier-V1.py is in.
 
The subfolders will be generated with the date and time they were created, and the individual files have a naming construct like so:
ID-<ID Number>_<Template File Name>_<ego_speed>_<other_speed>_<relative_distance_to_ego>.xosc
  
For the time being, the GUI is the only method of use but command-line use will be implemented in the near future.
  
If you come across any bugs or face any issues, please email me at: srahimi8@asu.edu
  
I hope it serves you well! 
  - Shujauddin Rahimi
