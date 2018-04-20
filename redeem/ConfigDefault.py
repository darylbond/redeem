"""
Default configuration for Redeem,

Author: Daryl Bond
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

from configobj import ConfigObj
from CascadingConfigParser import parse_capes
from Printer import Printer
import logging


def generate_default_config(file_name):
  """
  Generate the default configuration for the current hardware revision
  """

  replicape, reach = parse_capes()

  revision = replicape["rev"]
  reach_revision = reach["rev"]

  if revision:
    logging.info("Found Replicape rev. " + revision)
  else:
    logging.warning("Oh no! No Replicape present!")
    revision = "0B3A"

  # We set it to 5 axis by default
  NUM_AXES = 5
  if reach_revision:
    logging.info("Found Reach rev. " + reach_revision)
  if reach_revision == "00A0":
    NUM_AXES = 8
  elif reach_revision == "00B0":
    NUM_AXES = 7

  if revision in ["00A4", "0A4A", "00A3"]:
    PWM_FREQ = 100
  elif revision in ["00B1", "00B2", "00B3", "0B3A"]:
    PWM_FREQ = 1000

  axes = [a.lower() for a in Printer.axes_zipped[:NUM_AXES]]
  heaters = ["HBP"] + Printer.axes_zipped[3:NUM_AXES]

  cfg = ConfigObj(list_values=False, write_empty_values=True)

  #########
  # SYSTEM
  #########

  c = {}

  # CRITICAL=50, # ERROR=40, # WARNING=30,  INFO=20,  DEBUG=10, NOTSET=0
  c["loglevel"] = 20

  # If set to True, also log to file.
  c["log_to_file"] = True

  # Default file to log to, this can be viewed from octoprint
  c["logfile"] = "/home/octo/.octoprint/logs/plugin_redeem.log"

  # location to look for data files (temperature charts, etc)
  c["data_path"] = "/etc/redeem"

  # Plugin to load for redeem, comma separated (i.e. HPX2Max,plugin2,plugin3)
  c["plugins"] = ""

  # Machine type is used by M115
  # to identify the machine connected.
  c["machine_type"] = "Unknown"

  c["replicape_revision"] = revision

  c["pwm_freq"] = PWM_FREQ

  c["num_axes"] = NUM_AXES

  cfg["System"] = c

  #########
  # GEOMETRY
  #########

  c = {}

  # 0 - Cartesian
  # 1 - H-belt
  # 2 - Core XY
  # 3 - Delta
  c["axis_config"] = 0

  for a in axes:
    # The total length each axis can travel away
    # from its homing endstop. (negative references a max stop)
    # This affects the homing endstop searching length.
    c["travel_{}".format(a)] = 0.2

  # Define the origin in relation to the endstops.
  # The offset that the origin of the build plate has
  # from the end stop.
  c["offset_{}".format(a)] = 0.2

  c["bed_compensation_matrix"] = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

  cfg["Geometry"] = c

  #########
  # DELTA
  #########

  c = {}

  # Length of the rod
  c["L"] = 0.322
  # Radius of the columns
  c["r"] = 0.175

  # Compensation for positional error of the columns
  for a in ["A", "B", "C"]:
    # Radial offsets of the columns
    # Positive values move the tower away from the center of the printer
    c["{}_radial".format(a)] = 0.0

    # Angular offsets of the columns
    # Positive values move the tower counter-clockwise, as seen from above
    # Specified in degrees
    c["{}_angular".format(a)] = 0.0

  cfg["Delta"] = c

  #########
  # STEPPERS
  #########

  c = {}

  c["number_of_extruders"] = 2

  for a in axes:
    c["microstepping_{}".format(a)] = 3
    c["current_{}".format(a)] = 0.5

    # steps per mm:
    #   Defined how many stepper full steps needed to move 1mm.
    #   Do not factor in microstepping settings.
    #   For example: If the axis will travel 10mm in one revolution and
    #                angle per step in 1.8deg (200step/rev), steps_pr_mm is 20.
    c["steps_pr_mm_{}".format(a)] = 50.0

    c["backlash_{}".format(a)] = 0.0

    # Which steppers are enabled
    c["in_use_{}".format(a)] = True

    # Set to -1 if axis is inverted
    c["direction_{}".format(a)] = 1

    # Set to True if slow decay mode is needed
    c["slow_decay_{}".format(a)] = 0

    # A stepper controller can operate in slave mode,
    # meaning that it will mirror the position of the
    # specified stepper. Typically, H will mirror Y or Z,
    # in the case of the former, write this: slave_y = H.
    c["slave_{}".format(a)] = ""

    # Stepper timout
    c["use_timeout"] = True
    c["timeout_seconds"] = 500

  cfg["Steppers"] = c

  #########
  # PLANNER
  #########

  c = {}

  # size of the path planning cache
  c["move_cache_size"] = 1024

  # time to wait for buffer to fill, (ms)
  c["print_move_buffer_wait"] = 250

  # total buffered move time should not exceed this much (ms)
  c["max_buffered_move_time"] = 1000

  for a in axes:
    c["acceleration_{}".format(a)] = 0.5
    c["max_jerk_{}".format(a)] = 0.01

    # Max speed for the steppers in m/s
    c["max_speed_{}".format(a)] = 0.03

    # for arc commands, seperate into segments of length in m
    c["arc_segment_length"] = 0.001

    # When true, movements on the E axis (eg, G1, G92) will apply
    # to the active tool (similar to other firmwares).  When false,
    # such movements will only apply to the E axis.
    c["e_axis_active"] = True

  cfg["Planner"] = c

  #####################
  # TEMPERATURE CONTROL
  #####################

  c = {}

  # Thermal management is implemented in Redeem through a user configurable network
  # of sensors, heaters and fans. The user specifies the nodes of this network in this
  # section of the configuration file. Each node is a uniquely configured instance
  # from a pre-defined set, all of which are shown below. This approach allows
  # for a high degree of flexibility in setting up when fans turn on/off, the
  # type of control logic that is used for each heater/fan, and even allowing
  # multiple sensors to control their behaviour.
  #
  # allowed types are : alias, difference, maximum, minimum, constant-control,
  #   on-off-control, pid-control, proportional-control, safety, gcode

  # By default, we set 'active' = True for all units that are to be parsed. A False value means
  # that the unit will be ignored

  #
  # Templates for control units are given below.
  #
  #[[AliasUnitName]]
  #type = alias
  #input = <name of temperature sensor>
  #
  #[[ComparisonUnitName]]
  #type = difference, maximum, or minimum
  #input_0 = <name of input>
  #input_1 = <name of input>
  #
  #[[ConstantName]]
  #type = constant-control
  #value = <number in range 0..255>
  #output = <optional output target name>
  #
  #[[SafetyName]]
  #type = safety
  #max_rise_rate = <number, deg/sec>
  #max_fall_rate = <number, deg/sec>
  #min_temp = <number, deg>
  #max_temp = <number, deg>
  #min_rise_rate = <number, deg/sec>
  #min_rise_offset = <number, deg>
  #min_rise_delay = <number, sec>
  #input = <input sensor name>
  #heater = <heater name>
  #
  #[[OnOffName]]
  #type=on-off-control
  #target_value = <number>
  #on_offset = <number, turn on when value <= target + on_offset>
  #off_offset = <number, turn off when value >= target + off_offset>
  #on_value = <number in range 0..255>
  #off_value = <number in range 0..255>
  #sleep = <number, sec, time between control updates>
  #output = <optional output target name>
  #
  #
  #[[ProportionalControlName]]
  #type = proportional-control
  #input = <name of input>
  #target_value = <number, desired temperature>
  #Kp =  <number, proportional constant>
  #max_value = <number in range 0..255>
  #min_value = <number in range 0..255>
  #ok_range = <number, output=min_value if input is within ok_range of target>
  #sleep = <number, sec, time between control updates>
  #output = <optional output target name>
  #
  #[[PIDControlName]]
  #type = pid-control
  #input = <name of input>
  #target_value =  <number, desired temperature>
  #Kp =  <number, proportional constant>
  #Ti = <number, integral constant>
  #Td = <number, derivative constant>
  #ok_range = <number, output=0 if input is within ok_range of target>
  #on_off_range = <optional number, output max_value if input is less than target - on_off_range>
  #max_value = <number in range 0..255>
  #sleep = <number, sec, time between control updates>
  #output = <optional output target name>
  #
  #[[CommandName]]
  #type = gcode
  #command = <G- or M-code/s, multiple codes allowed as a comma separated list>
  #output = <output name/s, multiple outputs allowed as a comma separated list>
  #
  # NOTES:
  #   <> when connecting a control unit to a heater or fan the connection may be defined from either unit (input or output).
  #   <> 'difference' units return (input_0 - input_1)
  #   <> 'gcode' units currently only accept M106 or M107
  #   <> in 'safety' units the min_rise_* parameters are used to check for attached/detached/misconnected sensor/heater pairs
  #       when power is supplied to the heater, we expect min_rise_rate temperature rise per second, as long as temp is min_rise_offset
  #       below the heaters target temperature and we are min_rise_delay seconds after starting heating.
  #   <> multiple safety units may be attached to each heater but each safety can only define one input and one output
  #   <> safety inputs must be temperature sensors, or an alias thereof

  # Default setting is for all fans to be connected to M106/M107
  #  this means that the command 'M106 S255' will turn on all fans full blast
  #  to connect only selected fans edit the output list i.e. output = Fan_1
  #  Note that individual fan commands, such as 'M106 S255 P1', will always work
  #  (depending on the fan controller attached)

  cc = c["M106/M107"] = {}
  cc["type"] = "gcode"
  cc["command"] = "M106, M107"
  cc["output"] = ""

  # default PID control for heaters
  for h in heaters:
    cc = c["Control-{}".format(h)] = {}
    cc["type"] = "pid-control"
    cc["input"] = "Thermistor-{}".format(h)
    cc["target_value"] = 0.0
    cc["Kp"] = 0.1
    cc["Ti"] = 100.0
    cc["Td"] = 0.3
    cc["ok_range"] = 4.0
    cc["max_value"] = 255
    cc["sleep"] = 0.25

    # safety limits for heaters
    # multiple safety units may be attached to each heater
    # each safety only has one heater
    # these allow safety limits to be written for each temperature sensor

    # min_rise_* : when power is supplied to the heater, expect min_rise_temp
    #  temperature rise per second, as long as temp is min_rise_offset below the
    #  heaters target temperature

    cc = c["Safety-{}".format(h)] = {}
    cc["type"] = "safety"
    cc["max_rise_rate"] = 10.0
    cc["max_fall_rate"] = 10.0
    cc["min_temp"] = 20.0
    cc["max_temp"] = 250.0
    cc["min_rise_rate"] = 0.1
    cc["min_rise_offset"] = 20
    cc["min_rise_delay"] = 1
    cc["input"] = "Thermistor-{}".format(h)
    cc["heater"] = "Heater-{}".format(h)

  cfg["Temperature Control"] = c

  #####################
  # THERMISTORS
  #####################

  c = {}

  # Thermistors for measuring temperature
  # For list of available temp charts, look in temp_chart.py
  IDX = [6, 4, 5, 0, 3, 2]
  for i, h in enumerate(heaters):
    cc = c["Thermistor-{}".format(h)] = {}
    cc["sensor"] = "B57560G104F"
    cc["path_adc"] = "/sys/bus/iio/devices/iio:device0/in_voltage{}_raw".format(IDX[i])

  cfg["Thermistors"] = c

  #####################
  # FANS
  #####################

  c = {}

  # control the fans, hook them up to a temperature control unit or simply set
  # a constant value. Note that 'channel' is modified on startup according to
  # your Replicape version.

  # select the correct channel given the replicape revision
  channel = []
  if revision == "00A3":
    channels = [0, 1, 2]
  elif revision == "0A4A":
    channels = [8, 9, 10]
  elif revision in ["00B1", "00B2", "00B3", "0B3A"]:
    channels = [7, 8, 9, 10]
  if reach_revision == "00A0":
    channels = [14, 15, 7]

  for i, ch in enumerate(channels):
    cc = c["Fan-{}".format(i)] = {}
    cc["channel"] = ch
    cc["input"] = 0

  cfg["Fans"] = c

  #####################
  # HEATERS
  #####################

  c = {}

  # make things hot, can be connected to control units defined in [Temperature Control]
  # can have multiple safety units assigned to one heater i.e. safety = Safety-1, Safety-2

  IDX = [4, 5, 3, 11, 12, 13]
  prefix = ["B"] + ["T{}".format(i) for i in range(len(heaters) - 1)]
  for i, h in enumerate(heaters):
    cc = c["Heater-{}".format(h)] = {}
    cc["mosfet"] = IDX[i]
    cc["prefix"] = prefix[i]
    cc["input"] = "Control-{}".format(h)
    cc["safety"] = "Safety-{}".format(h)
    cc["stable_time"] = 5

  cfg["Heaters"] = c

  #####################
  # ENDSTOPS
  #####################

  c = {}

  # Which axis should be homed.
  for i, a in enumerate(axes):
    d = "has_{}".format(a)
    if i < 3:
      c[d] = True
    else:
      c[d] = False

  c["inputdev"] = "/dev/input/by-path/platform-ocp:gpio_keys-event"

  # Number of cycles to wait between checking
  # end stops. CPU frequency is 200 MHz
  c["end_stop_delay_cycles"] = 1000

  for x in ["X", "Y", "Z"]:
    for i in [1, 2]:
      # Invert =
      #   True means endstop is connected as Normally Open (NO) or not connected
      #   False means endstop is connected as Normally Closed (NC)
      c["invert_{}{}".format(x, i)] = False

      # If one endstop is hit, which steppers and directions are masked.
      #   The list is comma separated and has format
      #     x_cw = stepper x clockwise (independent of direction_x)
      #     x_ccw = stepper x counter clockwise (independent of direction_x)
      #     x_neg = setpper x negative direction (affected by direction_x)
      #     x_pos = setpper x positive direction (affected by direction_x)
      #   Steppers e and h (and a, b, c for reach) can also be masked.
      #
      #   For a list of steppers to stop, use this format: x_cw, y_ccw
      #   For Simple XYZ bot, the usual practice would be
      #     end_stop_X1_stops = x_neg, end_stop_X2_stops = x_pos, ...
      #   For CoreXY and similar, two steppers should be stopped if an end stop is hit.
      #     similarly for a delta probe should stop x, y and z.
      c["end_stop_{}{}_stops".format(x, i)] = ""

  c["pin_X1"] = "GPIO3_21"
  c["pin_X2"] = "GPIO0_30"

  c["pin_Y1"] = "GPIO1_17"
  if revision == "0A4A":
    c["pin_Y2"] = "GPIO1_19"
  else:
    c["pin_Y2"] = "GPIO3_17"

  c["pin_Z1"] = "GPIO0_31"
  c["pin_Z2"] = "GPIO0_4"

  c["keycode_X1"] = 112
  c["keycode_X2"] = 113
  c["keycode_Y1"] = 114
  c["keycode_Y2"] = 115
  c["keycode_Z1"] = 116
  c["keycode_Z2"] = 117

  # if an endstop should only be used for homing or probing, then add it to
  # homing_only_endstops in comma separated format.
  # Example: homing_only_endstops = Z1, Z2
  #   this will make sure that endstop Z1 and Z2 are only used during homing or probing
  # NOTE: Be very careful with this option.

  c["homing_only_endstops"] = ""

  for a in axes:
    c["soft_end_stop_min_{}".format(a)] = -1000.0
    c["soft_end_stop_max_{}".format(a)] = 1000.0

  cfg["Endstops"] = c

  #####################
  # HOMING
  #####################

  c = {}

  # default G28 homing axes
  c["G28_default_axes"] = "X,Y,Z,E,H,A,B,C"

  for a in axes:
    # Homing speed for the steppers in m/s
    #   Search to minimum ends by default. Negative value for searching to maximum ends.
    c["home_speed_{}".format(a)] = 0.1

    # homing backoff speed
    c["home_backoff_speed_{}".format(a)] = 0.01

    # homing backoff dist
    c["home_backoff_offset_{}".format(a)] = 0.01

    # Where should the printer goes after homing.
    # The default is to stay at the offset position.
    # This setting is useful if you have a delta printer
    # and want it to stay at the top position after homing, instead
    # of moving down to the center of the plate.
    # In that case, use home_z and set that to the same as the offset values
    # for X, Y, and Z, only with different sign.
    c["home_{}".format(a)] = 0.0

  cfg["Homing"] = c

  #####################
  # SERVOS
  #####################

  c = {}

  # Example servo for Rev A4A, connected to channel 14 on the PWM chip
  # For Rev B, servo is either P9_14 or P9_16.
  # Not enabled for now, just kept here for reference.
  # Angle init is the angle the servo is set to when redeem starts.
  # pulse min and max is the pulse with for min and max position, as always in SI unit Seconds.
  # So 0.001 is 1 ms.
  # Angle min and max is what angles those pulses correspond to.
  c["servo_0_enable"] = False
  c["servo_0_channel"] = "P9_14"
  c["servo_0_angle_init"] = 90
  c["servo_0_angle_min"] = -90
  c["servo_0_angle_max"] = 90
  c["servo_0_pulse_min"] = 0.001
  c["servo_0_pulse_max"] = 0.002

  cfg["Servos"] = c

  #####################
  # PROBE
  #####################

  c = {}

  c["length"] = 0.01
  c["speed"] = 0.05
  c["accel"] = 0.1
  c["offset_x"] = 0.0
  c["offset_y"] = 0.0
  c["offset_z"] = 0.0

  cfg["Probe"] = c

  #####################
  # ROTARY-ENCODERS
  #####################

  c = {}

  c["enable-e"] = False
  c["event-e"] = "/dev/input/event1"
  c["cpr-e"] = -360
  c["diameter-e"] = 0.003

  cfg["Rotary-encoders"] = c

  #####################
  # FILAMENT SENSORS
  #####################

  c = {}

  # If the error is > 1 cm, sound the alarm
  c["alarm-level-e"] = 0.01

  cfg["Filament-sensors"] = c

  #####################
  # WATCHDOG
  #####################

  c = {}

  c["enable_watchdog"] = True

  cfg["Watchdog"] = c

  #####################
  # ALARMS
  #####################

  cfg["Alarms"] = {}

  #####################
  # MACROS
  #####################

  c = {}

  c["G29"] = """
      M561                ; Reset the bed level matrix
      M558 P0             ; Set probe type to Servo with switch
      M557 P0 X10 Y20     ; Set probe point 0
      M557 P1 X10 Y180    ; Set probe point 1
      M557 P2 X180 Y100   ; Set probe point 2
      G28 X0 Y0           ; Home X Y
  
      G28 Z0              ; Home Z
      G0 Z12              ; Move Z up to allow space for probe
      G32                 ; Undock probe
      G92 Z0              ; Reset Z height to 0
      G30 P0 S            ; Probe point 0
      G0 Z0               ; Move the Z up
      G31                 ; Dock probe
  
      G28 Z0              ; Home Z
      G0 Z12              ; Move Z up to allow space for probe
      G32                 ; Undock probe
      G92 Z0              ; Reset Z height to 0
      G30 P1 S            ; Probe point 1
      G0 Z0               ; Move the Z up
      G31                 ; Dock probe
  
      G28 Z0              ; Home Z
      G0 Z12              ; Move Z up to allow space for probe
      G32                 ; Undock probe
      G92 Z0              ; Reset Z height to 0
      G30 P2 S            ; Probe point 2
      G0 Z0               ; Move the Z up
      G31                 ; Dock probe
  
      G28 X0 Y0           ; Home X Y"""

  c["G31"] = "M280 P0 S320 F3000  ; Probe up (Dock sled)"

  c["G32"] = "M280 P0 S-60 F3000  ; Probe down (Undock sled)"

  cfg["Macros"] = c

  #####################
  # HPX2MaxPlugin
  #####################

  c = {}
  # Configuration for the HPX2Max plugin (if loaded)

  # The channel on which the servo is connected. The numbering correspond to the Fan number
  c["servo_channel"] = 1

  # Extruder 0 angle to set the servo when extruder 0 is selected, in degree
  c["extruder_0_angle"] = 20

  # Extruder 1 angle to set the servo when extruder 1 is selected, in degree
  c["extruder_1_angle"] = 175

  cfg["HPX2MaxPlugin"] = c

  #####################
  # DualServoPlugin
  #####################

  c = {}

  # Configuration for the Dual extruder by servo plugin
  # This config is only used if loaded.

  # The pin name of where the servo is located
  c["servo_channel"] = "P9_14"
  c["pulse_min"] = 0.001
  c["pulse_max"] = 0.002
  c["angle_min"] = -90
  c["angle_max"] = 90
  c["extruder_0_angle"] = -5
  c["extruder_1_angle"] = 5

  cfg["DualServoPlugin"] = c

  #################################################################

  cfg.write(open(file_name, 'w'))
  logging.info("Written auto-generated default config to {}".format(file_name))

  return
