#!/usr/bin/env python3

#
# Copyright 2020 Henrik Halvorsen
#
# This file is part of Fuscus.
# 
# Fuscus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Fuscus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Fuscus.  If not, see <http://www.gnu.org/licenses/>.
#

import requests
import logging
import paho.mqtt.client as mqtt

class BrewfatherStream():
    def __init__(self, streamId, name, tempController, MQTT_broker=None, MQTT_gravity=None):
        print("Creating stream " + name + " on ID " + streamId)
        self.id = streamId
        self.name = name
        self.controller = tempController
        self.gravityTopic = MQTT_gravity
        self.gravity = 1.0
        if self.gravityTopic is not None:
            self._connection = mqtt.Client()
            self._connection.connect(str(MQTT_broker))
            self._connection.message_callback_add(self.gravityTopic, self.topicUpdate)
            result, self.mid = self._connection.subscribe(MQTT_gravity, 0)
            self._connection.loop_start()
    
    def topicUpdate(self, client, userdata, message):
        self.gravity = float(message.payload.decode("utf-8"))

    def push(self):
        data = {
            "name": self.name,
            "temp": self.controller.getBeerTemp(),
            "aux_temp": self.controller.getFridgeTemp(),
            "ext_temp": self.controller.getRoomTemp(),
            "temp_unit": "C",
            # "pressure": 0,
            # "pressure_unit": "PSI",
            # "ph": 7,
            # "bpm": 0,
            "comment": "Fuscus",
            "beer": "BeerFridge Beer"
        }
        if self.gravityTopic is not None:
            data["gravity"] = self.gravity
            data["gravity_unit"] = "G"
        print("Pushing to Brewfather:")
        logging.debug(data)
        response = requests.post("http://log.brewfather.net/stream?id="+self.id, data=data)
        print("Status code: ", response.status_code)