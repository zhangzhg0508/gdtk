#! /usr/bin/env python3
"""
First version of PITOT3. Still much to add...

Chris James (c.james4@uq.edu.au) - (01/01/21)

"""

import sys, os, math
import yaml

# I have put functions and classes on different lines here as it was getting too long
# TO DO: the functions could even be put in a functions file...
from pitot3_utils.pitot3_classes import Facility, Driver, Diaphragm, Facility_State, Tube, Nozzle, Test_Section
from pitot3_utils.pitot3_classes import eilmer4_CEAGas_input_file_creator, expansion_tube_test_time_calculator, state_output_for_final_output, pitot3_results_output

VERSION_STRING = '06-Sep-2021'

#-----------------------------------------------------------------------------------

def run_pitot3(config_dict = {}, config_filename = None, pitot3_data_folder = '$PITOT3_DATA'):

    print('-'*60)
    print ("Running PITOT3 version: {0}".format(VERSION_STRING))
    print('-'*60)

    print("Let's get started, shall we:")

    #--------------------------------------------------------------------------------
    # load the default config which loads everything which runs the program...

    default_config_yaml_filename = 'PITOT3_default_config.yaml'
    default_config_file = open(os.path.expandvars(pitot3_data_folder +  '/' + default_config_yaml_filename))
    default_config_data = yaml.load(default_config_file, Loader=yaml.FullLoader)

    # go through and any remove any None values which yaml has loaded as None
    for variable in default_config_data.keys():
        if default_config_data[variable] == 'None':
            default_config_data[variable] = None

    #--------------------------------------------------------------------------------
    # now load the user's config
    # TO DO: eventually make using a config file optional, so they can add it from a dictionary directly...
    # but I guess it will mainly come from a file, so maybe it is fine like this?

    if config_filename:

        user_config_yaml_filename = config_filename

        user_config_file = open(user_config_yaml_filename)
        user_config_data = yaml.load(user_config_file, Loader=yaml.FullLoader)

        for variable in user_config_data.keys():
            if user_config_data[variable] == 'None':
                user_config_data[variable] = None

    # --------------------------------------------------------------------------------
    # now merge the two config files from the input file and/or the config_dict, with the default config to get our overarching config
    # (giving preference to any user values over default ones by adding the user config second)
    # we also put the file config and the dictionary input config both here, with the dictionary updated last,
    # so it will overwrite file values with dictionary ones if both user inputs are used.

    config_data = {}
    config_data.update(default_config_data)
    if config_filename:
        config_data.update(user_config_data)
    config_data.update(config_dict)

    # we need to add the version string to the config dictionary for the final output
    config_data['VERSION_STRING'] = VERSION_STRING

    # --------------------------------------------------------------------------------
    # now pull out some variables which we need to get started....

    facilities_folder = config_data['facilities_folder']
    preset_gas_models_folder = config_data['preset_gas_models_folder']

    T_0 = float(config_data['T_0'])
    p_0 = float(config_data['p_0'])

    mode = config_data['mode']

    print("Calculation mode is '{0}'.".format(mode))

    # facility set up stuff
    if 'facility' in config_data:
        facility_name = config_data['facility']
    else:
        config_data['facility'] = None
        facility_name = None

    driver_condition_name = config_data['driver_condition']

    #-------------------------------------------------------------------------------
    # make the gas path list which we will append to as we go along to get everything in order during the calculation
    gas_path = []
    # also make the object_dict where we can store everything by name for when we need that too...
    object_dict = {}

    #--------------------------------------------------------------------------------
    # load facility
    if facility_name:
        print ("Chosen facility is '{0}'.".format(facility_name))

        facility_yaml_filename = '{0}/{1}.yaml'.format(facilities_folder, facility_name)
        facility_yaml_file = open(os.path.expandvars(facility_yaml_filename))
        facility_input_data = yaml.load(facility_yaml_file , Loader=yaml.FullLoader)

        # TO DO: this class should maybe take inputs instead of just taking the config file...
        facility = Facility(facility_input_data)

        # get some values which we may need while working through the calculation
        facility_type = facility.get_facility_type()
        secondary_driver_flag = facility.get_secondary_driver_flag()
        nozzle_flag = facility.get_nozzle_flag()

        # we also need to add the facility type to the config data so we have it later on...
        config_data['facility_type'] = facility_type

    else:

        facility = None

        # if there is no facility we need to get the facility_type, secondary_driver_flag and nozzle_flag from the config...
        facility_type = config_data['facility_type']
        secondary_driver_flag = config_data['secondary_driver']
        nozzle_flag = config_data['nozzle']

    print ("Facility type is '{0}'.".format(facility_type))

    if nozzle_flag:

        if 'area_ratio' in config_data:
            area_ratio = float(config_data['area_ratio'])
        else:
            # TO DO: need to throw some kind of exception here if they have not chosen a facility...
            # otherwise get the facility's geometric area ratio...
            area_ratio = facility.get_nozzle_geometric_area_ratio()
            print("User has not specified an area ratio, so the geometric area ratio of this facility's nozzle ({0}) will be used.".format(area_ratio))

    #-------------------------------------------------------------------------------------------------------
    # go through driver conditions
    # TO DO: this might be a useful method on the facility object? but isn't that useful here...

    # print ("Available facility driver conditions are:")
    #
    # for file in os.listdir('facilities/' + facility.get_driver_conditions_folder()):
    #     # print without the .yaml...
    #     print (file[:-5])
    #
    #     driver_condition_file_location = 'facilities/' + facility.get_driver_conditions_folder() + '/' + file
    #     driver_yaml_file = open(driver_condition_file_location)
    #     driver_condition_input_data = yaml.load(driver_yaml_file, Loader=yaml.FullLoader)
    #
    #     driver_condition = Driver_Condition(driver_condition_input_data)
    #     print(driver_condition.get_driver_condition_name())

    #-------------------------------------------------------------------------------------------------
    # pick a driver condition
    if driver_condition_name != 'custom':
        print("Chosen driver condition is '{0}'.".format(driver_condition_name))
        driver_condition_file_location = facilities_folder + '/' + facility.get_driver_conditions_folder() + '/' + driver_condition_name + '.yaml'
    else:
        print("Using custom driver condition from the file {0}.".format(config_data['driver_condition_filename']))
        driver_condition_file_location = config_data['driver_condition_filename']

    driver_yaml_file = open(os.path.expandvars(driver_condition_file_location))
    driver_condition_input_data = yaml.load(driver_yaml_file, Loader=yaml.FullLoader)

    # TO DO: I was thinking that it would be good to make this have lots of inputs, but it is almost too complicated
    # + it generally comes from a file...
    driver = Driver(driver_condition_input_data, p_0=p_0, T_0=T_0, preset_gas_models_folder = preset_gas_models_folder)

    state4 = driver.get_driver_rupture_state()
    print("Driver gas model is {0}.".format(state4.get_gas_state().gmodel.type_str))

    if state4.get_gas_state().gmodel.type_str == 'CEAGas':
        print("Driver gas composition is {0} (by mass) ({1}).".format(state4.get_reduced_species_massf_dict(),
                                                                      state4.get_gamma_and_R_string()))
    else:
        print("Driver gas {0}.".format(state4.get_gamma_and_R_string()))

    print ("Driver rupture conditions are p4 = {0:.2f} MPa, T4 = {1:.2f} K, M_throat = {2}.".format(state4.get_gas_state().p/1.0e6,
                                                                                                    state4.get_gas_state().T,
                                                                                                    driver.get_M_throat()))

    gas_path.append(driver)
    object_dict['driver'] = driver

    #-------------------------------------------------------------------------------------------------
    # now load / print out the final set up stuff before we get too far ahead of ourselves...
    # TO DO: all of this stuff should probably be rolled into a "start message" function or part of the code
    # so that we can add all of the various fill details which is not here currently...
    # (that may be hard without some changes to make the code set everything up and then make stuff run, but we will see
    # there may be some way)

    if secondary_driver_flag:
        # secondary driver stuff
        secondary_driver_gas_gas_model = config_data['secondary_driver_gas_gas_model']
        if secondary_driver_gas_gas_model != 'custom':
            secondary_driver_gas_name = config_data['secondary_driver_gas_name']
            secondary_driver_gas_filename = None
        else:
            secondary_driver_gas_name = None
            secondary_driver_gas_filename = config_data['secondary_driver_gas_filename']
        psd1 = float(config_data['psd1'])

        secondary_driver_fill_state_name = config_data['secondary_driver_fill_state_name']

        Tsd1 = config_data['Tsd1']

        if Tsd1 == 'T_0':
            Tsd1 = T_0

        # TO DO: I really need to make the gas objects etc. so that we can actually get more data here...

        if secondary_driver_gas_gas_model != 'custom':
            print("Secondary driver gas is {0}. Secondary driver gas gas model is {1}.".format(secondary_driver_gas_name, secondary_driver_gas_gas_model))
        else:
            print("Using custom secondary driver gas from the file {0}.".format(secondary_driver_gas_filename))
            print("Secondary driver gas gas model is {0}.".format(secondary_driver_gas_gas_model))

        print("Secondary driver fill pressure (p{0}) is {1:.2f} Pa.".format(secondary_driver_fill_state_name[1:], psd1))
        print("Secondary driver fill temperature (T{0}) is {1:.2f} K.".format(secondary_driver_fill_state_name[1:], Tsd1))

        if mode in ['fully_experimental']:
            vsd = float(config_data['vsd'])
            print("Selected secondary driver shock speed (vsd) is {0:.2f} m/s.".format(vsd))

    # shock tube stuff
    test_gas_gas_model = config_data['test_gas_gas_model']
    if test_gas_gas_model != 'custom':
        test_gas_name = config_data['test_gas_name']
        test_gas_filename = None
    else:
        test_gas_name = None
        test_gas_filename = config_data['test_gas_filename']
    p1 = float(config_data['p1'])

    shock_tube_fill_state_name = config_data['shock_tube_fill_state_name']

    T1 = config_data['T1']

    if T1 == 'T_0':
        T1 = T_0

    if test_gas_gas_model != 'custom':
        print("Test gas is {0}. Test gas gas model is {1}.".format(test_gas_name, test_gas_gas_model))
    else:
        print("Using custom test gas from the file {0}.".format(test_gas_filename))
        print("Test gas gas model is {0}.".format(test_gas_gas_model))
    print("Shock tube fill pressure (p{0}) is {1:.2f} Pa.".format(shock_tube_fill_state_name[1:], p1))
    print("Shock tube fill temperature (T{0}) is {1:.2f} K.".format(shock_tube_fill_state_name[1:], T1))

    if mode in ['fully_experimental', 'experimental_shock_tube_theoretical_acceleration_tube']:
        vs1 = float(config_data['vs1'])
        print("Selected shock tube shock speed (vs1) is {0:.2f} m/s.".format(vs1))

    if facility_type == 'expansion_tube':

        # acceleration tube stuff (we will let it have the default gas for now)

        accelerator_gas_gas_model = config_data['accelerator_gas_gas_model']
        if accelerator_gas_gas_model != 'custom':
            accelerator_gas_name = config_data['accelerator_gas_name']
            accelerator_gas_filename = None
        else:
            accelerator_gas_name = None
            accelerator_gas_filename = config_data['accelerator_gas_filename']

        p5 = float(config_data['p5'])

        acceleration_tube_fill_state_name = config_data['acceleration_tube_fill_state_name']

        T5 = config_data['T5']

        if T5 == 'T_0':
            T5 = T_0

        if accelerator_gas_gas_model != 'custom':
            print("Accelerator gas is {0}. Accelerator gas gas model is {1}.".format(accelerator_gas_name, accelerator_gas_gas_model))
        else:
            print("Using custom accelerator gas from the file {0}.".format(accelerator_gas_filename))
            print("Accelerator gas gas model is {0}.".format(accelerator_gas_gas_model))

        print("Acceleration tube fill pressure (p{0}) is {1:.2f} Pa.".format(acceleration_tube_fill_state_name[1:], p5))
        print("Acceleration tube fill temperature (T{0}) is {1:.2f} K.".format(acceleration_tube_fill_state_name[1:], T5))

        if mode in ['fully_experimental', 'theoretical_shock_tube_experimental_acceleration_tube']:
            vs2 = float(config_data['vs2'])
            print("Selected acceleration tube shock speed (vs2) is {0:.2f} m/s.".format(vs2))

    if nozzle_flag:
        print("Nozzle area ratio is {0}.".format(area_ratio))

    #-------------------------------------------------------------------------------------------------
    # pick a primary diaphragm model
    # TO DO: this is much simpler, so it should probably be given some inputs...

    primary_diaphragm_cfg = {'diaphragm_name':config_data['primary_diaphragm_name'],
                             'diaphragm_type':config_data['primary_diaphragm_diaphragm_type']}

    # now we add the diaphragm entrance state by getting the driver exit state...
    primary_diaphragm_cfg['diaphragm_entrance_state_name'] = gas_path[-1].get_exit_state_name()
    primary_diaphragm_cfg['diaphragm_entrance_state'] = gas_path[-1].get_exit_state()

    primary_diaphragm = Diaphragm(primary_diaphragm_cfg)

    gas_path.append(primary_diaphragm)
    object_dict['primary_diaphragm'] = primary_diaphragm

    #-------------------------------------------------------------------------------------------------
    # deal with the secondary driver if we are using it...
    if secondary_driver_flag:
        if facility:
            secondary_driver_length, secondary_driver_diameter = facility.get_secondary_driver_length_and_diameter()
        else:
            secondary_driver_length = None
            secondary_driver_diameter = None

        # now pull out some shock tube default values...
        secondary_driver_tube_name = config_data['secondary_driver_tube_name']
        secondary_driver_expand_to = config_data['secondary_driver_expand_to']
        secondary_driver_expansion_factor = config_data['secondary_driver_expansion_factor']

        secondary_driver_unsteady_expansion_steps = config_data['secondary_driver_unsteady_expansion_steps']
        vsd_guess_1 = config_data['vsd_guess_1']
        vsd_guess_2 = config_data['vsd_guess_2']
        vsd_limits = config_data['vsd_limits']
        vsd_tolerance = config_data['vsd_tolerance']

        secondary_driver_shocked_state_name = config_data['secondary_driver_shocked_state_name']
        secondary_driver_unsteadily_expanded_state_name = config_data['secondary_driver_unsteadily_expanded_state_name']

        secondary_driver = Tube(tube_name=secondary_driver_tube_name, tube_length=secondary_driver_length, tube_diameter=secondary_driver_diameter,
                                fill_pressure=psd1, fill_temperature=Tsd1, fill_gas_model=secondary_driver_gas_gas_model,
                                fill_gas_name=secondary_driver_gas_name, fill_gas_filename=secondary_driver_gas_filename,
                                fill_state_name=secondary_driver_fill_state_name,
                                shocked_fill_state_name=secondary_driver_shocked_state_name,
                                entrance_state_name=gas_path[-1].get_exit_state_name(),
                                entrance_state=gas_path[-1].get_exit_state(),
                                unsteadily_expanded_entrance_state_name=secondary_driver_unsteadily_expanded_state_name,
                                expand_to=secondary_driver_expand_to, expansion_factor=secondary_driver_expansion_factor,
                                preset_gas_models_folder=preset_gas_models_folder,
                                unsteady_expansion_steps=secondary_driver_unsteady_expansion_steps,
                                vs_guess_1=vsd_guess_1, vs_guess_2=vsd_guess_2, vs_limits=vsd_limits, vs_tolerance=vsd_tolerance)

        gas_path.append(secondary_driver)
        object_dict['secondary_driver'] = secondary_driver

        if mode in ['fully_theoretical']:
            secondary_driver.calculate_shock_speed_and_related_states()
        elif mode in ['fully_experimental']:
            secondary_driver.set_shock_speed_and_calculate_related_states(vsd)

        # and we have another diaphragm here too...
        secondary_diaphragm_cfg = {'diaphragm_name':config_data['secondary_diaphragm_name'],
                                   'diaphragm_type':config_data['secondary_diaphragm_diaphragm_type'],
                                   'Mr_input':config_data['secondary_diaphragm_Mr'],
                                   'velocity_loss_factor':config_data['secondary_diaphragm_velocity_loss_factor']}

        # now we add the diaphragm entrance state by getting the shock tube exit state...
        secondary_diaphragm_cfg['diaphragm_entrance_state_name'] = gas_path[-1].get_exit_state_name()
        secondary_diaphragm_cfg['diaphragm_entrance_state'] = gas_path[-1].get_exit_state()

        secondary_diaphragm = Diaphragm(secondary_diaphragm_cfg)

        gas_path.append(secondary_diaphragm)
        object_dict['secondary_diaphragm'] = secondary_diaphragm

    #-------------------------------------------------------------------------------------------------
    # now deal with the shock tube...

    if facility:
        shock_tube_length, shock_tube_diameter = facility.get_shock_tube_length_and_diameter()
    else:
        shock_tube_length = None
        shock_tube_diameter = None

    # now pull out some shock tube default values...
    shock_tube_tube_name = config_data['shock_tube_tube_name']
    shock_tube_expand_to = config_data['shock_tube_expand_to']
    shock_tube_expansion_factor = config_data['shock_tube_expansion_factor']

    shock_tube_unsteady_expansion_steps = config_data['shock_tube_unsteady_expansion_steps']
    vs1_guess_1 = config_data['vs1_guess_1']
    vs1_guess_2 = config_data['vs1_guess_2']
    vs1_limits = config_data['vs1_limits']
    vs1_tolerance = config_data['vs1_tolerance']

    shock_tube_shocked_state_name = config_data['shock_tube_shocked_state_name']
    shock_tube_unsteadily_expanded_state_name = config_data['shock_tube_unsteadily_expanded_state_name']

    shock_tube = Tube(tube_name = shock_tube_tube_name, tube_length = shock_tube_length, tube_diameter = shock_tube_diameter,
                      fill_pressure = p1, fill_temperature = T1, fill_gas_model = test_gas_gas_model,
                      fill_gas_name = test_gas_name, fill_gas_filename = test_gas_filename,
                      fill_state_name = shock_tube_fill_state_name, shocked_fill_state_name = shock_tube_shocked_state_name,
                      entrance_state_name = gas_path[-1].get_exit_state_name(),
                      entrance_state = gas_path[-1].get_exit_state(),
                      unsteadily_expanded_entrance_state_name = shock_tube_unsteadily_expanded_state_name,
                      expand_to = shock_tube_expand_to, expansion_factor = shock_tube_expansion_factor,
                      preset_gas_models_folder = preset_gas_models_folder,
                      unsteady_expansion_steps = shock_tube_unsteady_expansion_steps,
                      vs_guess_1 = vs1_guess_1, vs_guess_2 = vs1_guess_2, vs_limits = vs1_limits, vs_tolerance = vs1_tolerance)

    gas_path.append(shock_tube)
    object_dict['shock_tube'] = shock_tube

    if mode in ['fully_theoretical', 'theoretical_shock_tube_experimental_acceleration_tube']:
        shock_tube.calculate_shock_speed_and_related_states()
    elif mode in ['fully_experimental', 'experimental_shock_tube_theoretical_acceleration_tube']:
        shock_tube.set_shock_speed_and_calculate_related_states(vs1)

    if facility_type == 'reflected_shock_tunnel':
        shock_tube.calculate_rst_stagnation_conditions()

    #---------------------------------------------------------------------------------------------
    # now the secondary or tertiary diaphragm...
    # TO DO: I would like to improve this to make it work better with the set up...

    # TO DO: I probably need to remove the cfg file input here, as it doesn't really work that well
    # (and I didn't do it for the tubes which are much more complicated...

    if not secondary_driver_flag:

        secondary_diaphragm_cfg = {'diaphragm_name':config_data['secondary_diaphragm_name'],
                                   'diaphragm_type':config_data['secondary_diaphragm_diaphragm_type'],
                                   'Mr_input':config_data['secondary_diaphragm_Mr'],
                                   'velocity_loss_factor':config_data['secondary_diaphragm_velocity_loss_factor']}

        # now we add the diaphragm entrance state by getting the shock tube exit state...
        secondary_diaphragm_cfg['diaphragm_entrance_state_name'] = gas_path[-1].get_exit_state_name()
        secondary_diaphragm_cfg['diaphragm_entrance_state'] = gas_path[-1].get_exit_state()

        secondary_diaphragm = Diaphragm(secondary_diaphragm_cfg)

        gas_path.append(secondary_diaphragm)
        object_dict['secondary_diaphragm'] = secondary_diaphragm

    else:
        # this is the tertiary diaphragm...
        tertiary_diaphragm_cfg = {'diaphragm_name':config_data['tertiary_diaphragm_name'],
                                  'diaphragm_type':config_data['tertiary_diaphragm_diaphragm_type'],
                                  'Mr_input':config_data['tertiary_diaphragm_Mr'],
                                  'velocity_loss_factor':config_data['tertiary_diaphragm_velocity_loss_factor']}

        # now we add the diaphragm entrance state by getting the shock tube exit state...
        tertiary_diaphragm_cfg['diaphragm_entrance_state_name'] = gas_path[-1].get_exit_state_name()
        tertiary_diaphragm_cfg['diaphragm_entrance_state'] = gas_path[-1].get_exit_state()

        tertiary_diaphragm = Diaphragm(tertiary_diaphragm_cfg)

        gas_path.append(tertiary_diaphragm)
        object_dict['tertiary_diaphragm'] = tertiary_diaphragm

    if facility_type == 'expansion_tube':

        #---------------------------------------------------------------------------------------------
        # now we deal with the acceleration tube...

        if facility:
            acceleration_tube_length, acceleration_tube_diameter = facility.get_acceleration_tube_length_and_diameter()
        else:
            acceleration_tube_length = None
            acceleration_tube_diameter = None

        # now pull out some acceleration tube default values...
        acceleration_tube_tube_name = config_data['acceleration_tube_tube_name']
        acceleration_tube_expand_to = config_data['acceleration_tube_expand_to']
        acceleration_tube_expansion_factor = config_data['acceleration_tube_expansion_factor']

        acceleration_tube_unsteady_expansion_steps = config_data['acceleration_tube_unsteady_expansion_steps']
        vs2_guess_1 = config_data['vs2_guess_1']
        vs2_guess_2 = config_data['vs2_guess_2']
        vs2_limits = config_data['vs2_limits']
        vs2_tolerance = config_data['vs2_tolerance']

        acceleration_tube_shocked_state_name = config_data['acceleration_tube_shocked_state_name']
        acceleration_tube_unsteadily_expanded_state_name = config_data['acceleration_tube_unsteadily_expanded_state_name']

        # TO DO: could add some print statements here to show what has been changed...
        # now replace any values which reference vs1 with the found vs1 value...
        if isinstance(vs2_guess_1, str) and 'vs1' in vs2_guess_1:
            vs2_guess_1_split = vs2_guess_1.split('+')

            vs2_guess_1 = 0.0

            for value in vs2_guess_1_split:
                if value.strip() == 'vs1':
                    vs2_guess_1 += shock_tube.get_shock_speed()
                else:
                    vs2_guess_1 += float(value.strip())

        if isinstance(vs2_guess_2, str) and 'vs1' in vs2_guess_2:
            vs2_guess_2_split = vs2_guess_2.split('+')

            vs2_guess_2 = 0.0

            for value in vs2_guess_2_split:
                if value.strip() == 'vs1':
                    vs2_guess_2 += shock_tube.get_shock_speed()
                else:
                    vs2_guess_2 += float(value.strip())

        if vs2_limits[0] == 'vs1':
            vs2_limits[0] = shock_tube.get_shock_speed()

        acceleration_tube = Tube(tube_name = acceleration_tube_tube_name,
                                 tube_length = acceleration_tube_length, tube_diameter = acceleration_tube_diameter,
                                 fill_pressure = p5, fill_temperature = T5, fill_gas_model = accelerator_gas_gas_model,
                                 fill_gas_name = accelerator_gas_name, fill_gas_filename = accelerator_gas_filename,
                                 fill_state_name = acceleration_tube_fill_state_name,
                                 shocked_fill_state_name = acceleration_tube_shocked_state_name,
                                 entrance_state_name = gas_path[-1].get_exit_state_name(),
                                 entrance_state = gas_path[-1].get_exit_state(),
                                 unsteadily_expanded_entrance_state_name = acceleration_tube_unsteadily_expanded_state_name,
                                 expand_to = acceleration_tube_expand_to, expansion_factor = acceleration_tube_expansion_factor,
                                 preset_gas_models_folder = preset_gas_models_folder,
                                 unsteady_expansion_steps = acceleration_tube_unsteady_expansion_steps,
                                 vs_guess_1 = vs2_guess_1, vs_guess_2 = vs2_guess_2, vs_limits = vs2_limits, vs_tolerance = vs2_tolerance)

        gas_path.append(acceleration_tube)
        object_dict['acceleration_tube'] = acceleration_tube

        if mode in ['fully_theoretical', 'experimental_shock_tube_theoretical_acceleration_tube']:
            acceleration_tube.calculate_shock_speed_and_related_states()
        elif mode in ['fully_experimental', 'theoretical_shock_tube_experimental_acceleration_tube']:
            acceleration_tube.set_shock_speed_and_calculate_related_states(vs2)

    #--------------------------------------------------------------------------------------------
    # now the nozzle

    if nozzle_flag:

        nozzle_expansion_tolerance = config_data['nozzle_expansion_tolerance']
        nozzle_exit_state_name = config_data['nozzle_exit_state_name']

        nozzle = Nozzle(entrance_state_name=gas_path[-1].get_exit_state_name(),
                        entrance_state=gas_path[-1].get_exit_state(),
                        exit_state_name=nozzle_exit_state_name, area_ratio=area_ratio,
                        nozzle_expansion_tolerance=nozzle_expansion_tolerance,
                        facility_type = facility_type)

        gas_path.append(nozzle)
        object_dict['nozzle'] = nozzle

    #--------------------------------------------------------------------------------------------
    # test section state

    test_section_post_shock_state_name = config_data['test_section_post_shock_state_name']

    test_section = Test_Section(entrance_state_name=gas_path[-1].get_exit_state_name(),
                                entrance_state=gas_path[-1].get_exit_state(),
                                test_section_post_shock_state_name=test_section_post_shock_state_name)

    gas_path.append(test_section)
    object_dict['test_section'] = test_section

    test_section.calculate_post_normal_shock_state()

    if 'cone_half_angle_degrees' in config_data:
        cone_half_angle_degrees = config_data['cone_half_angle_degrees']
        # cone calculation is not working at the moment...
        test_section.calculate_post_conical_shock_state(cone_half_angle_degrees)

    if 'wedge_angle_degrees' in config_data:
        wedge_angle_degrees = config_data['wedge_angle_degrees']
        test_section.calculate_post_wedge_shock_state(wedge_angle_degrees=wedge_angle_degrees)

    #--------------------------------------------------------------------------------------------
    # now do the final output

    pitot3_results_output(config_data, gas_path, object_dict)

    return config_data, gas_path, object_dict


# ----------------------------------------------------------------------------

def main():
    import optparse
    op = optparse.OptionParser(version=VERSION_STRING)
    op.add_option('-c', '--config_filename', '--config-filename', dest='config_filename',
                  help=("filename where the user configuration file is located"))

    opt, args = op.parse_args()
    config_filename = opt.config_filename

    run_pitot3(config_filename=config_filename)

# ----------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print ("PITOT3  - Equilibrium impulse facility simulator")
        print ("start with --help for help with inputs")

    else:
        main()