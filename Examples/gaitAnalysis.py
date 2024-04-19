'''
    ---------------------------------------------------------------------------
    OpenCap processing: example_gait_analysis.py
    ---------------------------------------------------------------------------
    Copyright 2023 Stanford University and the Authors
    
    Author(s): Scott Uhlrich
    
    Licensed under the Apache License, Version 2.0 (the "License"); you may not
    use this file except in compliance with the License. You may obtain a copy
    of the License at http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
                
    Please contact us for any questions: https://www.opencap.ai/#contact

    This example shows how to run a kinematic analysis of gait data. It works
    with either treadmill or overground gait. You can compute scalar metrics 
    as well as gait cycle-averaged kinematic curves.
    
'''

import os
import sys
import numpy as np
import math
import zipfile
import tkinter as tk
import csv

sys.path.append(os.path.abspath("./"))
sys.path.append(os.path.abspath("./ActivityAnalyses"))

from tkinter import filedialog
from gait_analysis import gait_analysis
from utils import get_trial_id, download_trial
from utilsPlotting import plot_dataframe_with_shading


# %% Paths.
#baseDir = os.path.join(os.getcwd(), '..')
#dataFolder = os.path.join(baseDir, 'Data')

# %% GDI Variables
with open(r'C:\Users\loshea\repo\matrix.csv', 'r') as file:
    matrix = list(csv.reader(file))
matrix = np.array(matrix, dtype=float)
#matrix = matrix.reshape((459,21))
matrix = np.transpose(np.array(matrix))

with open(r'C:\Users\loshea\repo\perGaitCycle.csv', 'r') as file:
    perGaitCycle = list(csv.reader(file))
    
with open(r'C:\Users\loshea\repo\controlCalc.csv', 'r') as file:
    controlCalc = csv.reader(file)
    controlCalc = [float(value) for row in controlCalc for value in row]
    
# %% User-defined variables.
# Select example: options are treadmill and overground.
# example = 'overground'

# if example == 'treadmill':
#     session_id = '4d5c3eb1-1a59-4ea1-9178-d3634610561c' # 1.25m/s
#     trial_name = 'walk_1_25ms'

# elif example == 'overground':
#     session_id = 'b39b10d1-17c7-4976-b06c-a6aaf33fead2'
#     trial_name = 'gait_3'


# %% select and unzip downloaded folder
root = tk.Tk()
root.withdraw()
filePath = filedialog.askopenfilename()

with zipfile.ZipFile(filePath, 'r') as zip_ref:
    zip_ref.extractall(filePath[:filePath.find("_")])

if filePath:
    firstInd = filePath.find("Data_") + len("Data_")
    session_id = filePath[firstInd:filePath.find("_",firstInd)]
else:
    print("No file selected.")



while True:
        #look for trial names
    trialNames = []
    for root, dirs, files in os.walk(filePath[:filePath.find("_")]):
        for file in files:
            if file.endswith(".trc"):
                trialNames.append(file[:-4])
                
    print()
    print("Available trials:")
    for i, trial in enumerate(trialNames, start=1):
        print(f"{i}. {trial}")
    
    while True:
        try:
            selected_index = int(input("Enter the index of the trial to run: "))-1
            if 0 <= selected_index < len(trialNames):
                trial_name = trialNames[selected_index]
                break
        except ValueError:
            print("Invalid input")
    
    print(trial_name)
    print()
    
    scalar_names = {'gait_speed', 'stride_length', 'step_width', 'cadence',
                    'single_support_time', 'double_support_time', 'step_length_symmetry'}
    
    # Select how many gait cycles you'd like to analyze. Select -1 for all gait
    # cycles detected in the trial.
    n_gait_cycles = -1
    
    # Select lowpass filter frequency for kinematics data.a
    filter_frequency = 6
    trimming_start = -1
    trimming_end = -1
    # %% Gait analysis.
    # Get trial id from name.
    trial_id = get_trial_id(session_id, trial_name)
    
    # Set session path.
    sessionDir = os.path.join(dataFolder, session_id)
    
    # Download data.
    trialName = download_trial(trial_id, sessionDir, session_id=session_id)
    
    
    # Init gait analysis.
    gait_r = gait_analysis(
        sessionDir, trialName, leg='r',
        lowpass_cutoff_frequency_for_coordinate_values=filter_frequency,
        n_gait_cycles=n_gait_cycles, trimming_start=trimming_start, trimming_end=trimming_end)
    gait_l = gait_analysis(
        sessionDir, trialName, leg='l',
        lowpass_cutoff_frequency_for_coordinate_values=filter_frequency,
        n_gait_cycles=n_gait_cycles, trimming_start=trimming_start, trimming_end=trimming_end)
    
    # Compute scalars and get time-normalized kinematic curves.
    gaitResults = {}
    gaitResults['scalars_r'] = gait_r.compute_scalars(scalar_names)
    gaitResults['curves_r'] = gait_r.get_coordinates_normalized_time()
    gaitResults['scalars_l'] = gait_l.compute_scalars(scalar_names)
    gaitResults['curves_l'] = gait_l.get_coordinates_normalized_time()
    
    # %% Print scalar results.
    print('\nRight foot gait metrics:')
    print('-----------------')
    for key, value in gaitResults['scalars_r'].items():
        rounded_value = round(value['value'], 2)
        print(f"{key}: {rounded_value} {value['units']}")
    
    print('\nLeft foot gait metrics:')
    print('-----------------')
    for key, value in gaitResults['scalars_l'].items():
        rounded_value = round(value['value'], 2)
        print(f"{key}: {rounded_value} {value['units']}")
    
    # %% You can plot multiple curves, in this case we compare right and left legs.
    
    joint_names = ['pelvis_tilt', 'pelvis_list', 'pelvis_rotation', 'hip_flexion_r',
                   'hip_adduction_r', 'hip_rotation_r', 'knee_angle_r', 'ankle_angle_r', 'subtalar_angle_r']
    data = []
    
    for k in joint_names:
           for num in range(101):
                if (num % 2 == 0):
                     if (k == 'pelvis_tilt'):
                          #print(gaitResults['curves_r']['mean'][k][num]+20)
                          data.append(gaitResults['curves_r']['mean'][k][num]+20)
                     elif (k == 'pelvis_rotation'):
                          if (gaitResults['curves_r']['mean'][k][num] > 180):
                              data.append(
                                  (gaitResults['curves_r']['mean'][k][num]-180))
                              #print((gaitResults['curves_r']['mean'][k][num]-180))
                          else:
                              data.append(gaitResults['curves_r']['mean'][k][num])
                              #print(gaitResults['curves_r']['mean'][k][num])
                     else:
                          data.append(gaitResults['curves_r']['mean'][k][num])
                          #print(gaitResults['curves_r']['mean'][k][num])
    
    # % Calculate the GDI
    value = np.array(data)
    subject = np.dot(matrix, value)
    diff = subject - controlCalc
    
    ln_result = math.log(math.sqrt(np.sum(np.square(diff)) ))  # natural log of the euclidean distance between subjects and controls
    z_score = (ln_result - 4.443685139)/0.223457646 #The z-score is found by subtracting the average natural log accross all subjects to the ln_result and dividing by the SD of the average NL
    GDI_r = 100 - (10*z_score)
    print()
    print("Right GDI: ")
    print(GDI_r)
    #uncomment the print lines if you want to check GDI score with excel sheet
    
    joint_names2 =['pelvis_tilt', 'pelvis_list', 'pelvis_rotation', 'hip_flexion_l', 
    'hip_adduction_l', 'hip_rotation_l', 'knee_angle_l', 'ankle_angle_l', 'subtalar_angle_l']
    data = []
    
    for k in joint_names2:
        for num in range(101):
            if (num % 2 == 0):
                if (k == 'pelvis_tilt'):
                    #print(gaitResults['curves_l']['mean'][k][num]+20)
                    data.append(gaitResults['curves_l']['mean'][k][num]+20)
                elif (k =='pelvis_rotation'):
                    if (gaitResults['curves_l']['mean'][k][num] >180):
                        #print((gaitResults['curves_l']['mean'][k][num]-180))
                        data.append((gaitResults['curves_l']['mean'][k][num]-180))
                    else:
                        #print(gaitResults['curves_l']['mean'][k][num])
                        data.append(gaitResults['curves_l']['mean'][k][num])
                else:
                    #print(gaitResults['curves_l']['mean'][k][num])
                    data.append(gaitResults['curves_l']['mean'][k][num])
    
    # % Calculate the GDI
    value = np.array(data)
    subject = np.dot(matrix, value)
    diff = subject - controlCalc
    
    ln_result = math.log(math.sqrt(np.sum(np.square(diff)) ))  # natural log of the euclidean distance between subjects and controls
    z_score = (ln_result - 4.443685139)/0.223457646 #The z-score is found by subtracting the average natural log accross all subjects to the ln_result and dividing by the SD of the average NL
    GDI_l = 100 - (10*z_score)
    print()
    print("Left GDI: ")
    print(GDI_l)
    
    
    #get the GDI average
    avg = (GDI_r + GDI_l)/2
    print()
    print("Average GDI: ")
    print(avg)
    print()
    
    plot_dataframe_with_shading(
        [gaitResults['curves_r']['mean'], gaitResults['curves_l']['mean']],
        [gaitResults['curves_r']['sd'], gaitResults['curves_l']['sd']],
        leg = ['r', 'l'],
        xlabel= '% gait cycle',
        title= 'kinematics (m or deg)',
        legend_entries = ['right', 'left'])
    
    #ask user if they want to run another trial
    response = input("Do you want to run another trial? [Y/N]: ").lower()
    
    if response != 'y':
        break
    
