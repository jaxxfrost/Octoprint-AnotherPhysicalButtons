# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.events import Events
import RPi.GPIO as GPIO
from datetime import date
import datetime
import time
from time import sleep
# from flask import jsonify
import octoprint.util

class AnotherphysicalbuttonsPlugin(octoprint.plugin.StartupPlugin,
                                    octoprint.plugin.EventHandlerPlugin,
                                    octoprint.plugin.SettingsPlugin,
                                    octoprint.plugin.AssetPlugin,
                                    octoprint.plugin.TemplatePlugin):

    light_toggle = False
    stopped_triggered = False
    monitor_active = False
    bouncetime_button = 400
    printer_is_hot = False   
    bed_level_stage = 0
    
    def on_after_startup(self):
        self._logger.info("Another Physical Buttons %s started", self._plugin_version)
        self.setup_gpios()

    def setup_gpios(self):
        self._logger.info("Setting up GPIO channels")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)        
        GPIO.setup(35, GPIO.OUT)
        self.setup_gpio(self.heatup_pin) #yellow
        self.setup_gpio(self.disengage_pin)     #white   
        self.setup_gpio(self.home_pin) #green 
        self.setup_gpio(self.levelbed_pin) #black
        self.setup_gpio(self.up_pin) #blue
        self.setup_gpio(self.pause_pin)   #red        

    def setup_gpio(self, channel):
        self._logger.debug("Starting setup_gpio")
        try:
            if channel != -1:
 
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.remove_event_detect(channel)
                GPIO.add_event_detect(
                    channel, GPIO.RISING,
                    callback=self.button_callback,
                    bouncetime=self.debounce)

        except:
            self._logger.exception("Cannot setup GPIO port %s for input, already assigned?", str(channel))        

        self._logger.info("Done setup_gpios for GPIO pin [%s]" % str(channel))

    def button_callback(self, channel):
        self._logger.info("Change state on pin %s called", str(channel))
        self.light_toggle = not self.light_toggle
        GPIO.output(35, self.light_toggle)        
        if channel == self.heatup_pin:

            if self.printer_is_hot == True:
                self._printer.commands("M117 Nozzle Cooling")
                self._printer.set_temperature("tool0", 0)
                self._printer.commands("M117 Bed Cooling")
                self._printer.set_temperature("bed", 0)                
                self._logger.info("Heat up / off button pressed. Printer was hot, cooling now")
                self.printer_is_hot = False

            else:
                self._printer.commands("M117 Nozzle Heating")
                self._printer.set_temperature("tool0", self.nozzle_temp)
                self._printer.commands("M117 Bed Heating")
                self._printer.set_temperature("bed", self.bed_temp)                
                self._logger.info("Heat up / off button pressed.  Printer was cool, heating now")
                self.printer_is_hot = True                

        if channel == self.disengage_pin:
            self._logger.debug("Disengage pressed")
            self._printer.commands("M18")

        if channel == self.home_pin:
            self._logger.debug("Disengage pin pressed")
            d = {'z' :10}
            self._printer.jog(d)
            self._printer.home("x")
            self._printer.home("y")
            self._printer.home("z")

        if channel == self.levelbed_pin:

            self._logger.debug("Level bed pressed")
            if self.bed_level_stage == 0:
                d = {'z' :10}
                self._printer.jog(d)
                self._printer.home("x")
                self._printer.home("y")
                self._printer.home("z")        

            elif self.bed_level_stage == 1:
                d = {'z' :10}
                self._printer.jog(d)
                self._printer.home("y")                
                self._printer.commands("G0 X350")                
                self._printer.home("z")

            elif self.bed_level_stage == 2:
                d = {'z' :10}
                self._printer.jog(d)
                self._printer.commands("G0 X350")            
                self._printer.commands("G0 Y350")                
                self._printer.home("z")

            elif self.bed_level_stage == 3:
                d = {'z' :10}
                self._printer.jog(d)
                self._printer.home("x")                
                self._printer.home("z")
                self.bed_level_stage = -1

            self.bed_level_stage = self.bed_level_stage + 1                            

        if channel == self.up_pin:
            self._logger.debug("Z up pressed")
            d = {'z' :self.z_increment}
            self._printer.jog(d)

        if channel == self.pause_pin:
            self._logger.debug("Pause pressed")
            self._printer.pause_print
            
    def on_settings_save(self, data):
        self._logger.info("Saving settings")
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)        


    def get_settings_defaults(self):
        return dict(
            debounce=250,  # Debounce 100ms
            pause_pin=21,  # seconds
            no_filament_gcode='',  #
            stopped_pause_print=False,  # Debounce 250ms
            heatup_pin=-1,  # Disabled
            disengage_pin=-1,  # Disabled
            home_pin=-1,  # Disabled
            levelbed_pin=-1,  # Disabled
            up_pin=-1,     
            nozzle_temp=190,
            bed_temp=45,
            z_increment=20,   
        )

    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    def get_assets(self):
        return {
            "js": ["js/anotherphysicalbuttons.js"],
            "css": ["css/anotherphysicalbuttons.css"],
            "less": ["less/anotherphysicalbuttons.less"]
        }

    @property
    def debounce(self):
        return int(self._settings.get(["debounce"]))

    @property
    def heatup_pin(self):
        return int(self._settings.get(["heatup_pin"]))

    @property
    def disengage_pin(self):
        return int(self._settings.get(["disengage_pin"]))

    @property
    def home_pin(self):
        return int(self._settings.get(["home_pin"]))

    @property
    def levelbed_pin(self):
        return int(self._settings.get(["levelbed_pin"]))        

    @property
    def up_pin(self):
        return int(self._settings.get(["up_pin"]))

    @property
    def pause_pin(self):
        return int(self._settings.get(["pause_pin"]))

    @property
    def nozzle_temp(self):
        return int(self._settings.get(["nozzle_temp"]))

    @property
    def bed_temp(self):
        return int(self._settings.get(["bed_temp"]))

    @property
    def z_increment(self):
        return int(self._settings.get(["z_increment"]))


    def get_update_information(self):
        return {
            "anotherphysicalbuttons": {
                "displayName": "Anotherphysicalbuttons Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "jaxxfrost",
                "repo": "OctoPrint-Anotherphysicalbuttons",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/jaxxfrost/OctoPrint-Anotherphysicalbuttons/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "Another Physical Buttons"

__plugin_pythoncompat__ = ">=3,<4" # only python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = AnotherphysicalbuttonsPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
