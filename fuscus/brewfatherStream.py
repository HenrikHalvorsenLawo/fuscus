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

import json
import requests
import logging

class BrewfatherStream():
    def __init__(self, streamId, name, tempController):
        print("Creating stream " + name + " on ID " + streamId)
        self.id = streamId
        self.name = name
        self.controller = tempController

    def push(self):
        data = {
            "name": self.name,
            "temp": self.controller.getBeerTemp(),
            "aux_temp": self.controller.getFridgeTemp(),
            "ext_temp": self.controller.getRoomTemp(),
            "temp_unit": "C",
            "gravity": 1.000,
            "gravity_unit": "G",
            "pressure": 0,
            "pressure_unit": "PSI",
            "ph": 7,
            "bpm": 0,
            "comment": "Fuscus",
            "beer": "BeerFridge Beer"
        }
        jsonData = json.dumps(data)
        print("Pushing to Brewfather:")
        logging.debug(jsonData)
        response = requests.post("http://log.brewfather.net/stream?id="+self.id, json=jsonData)
        print("Status code: ", response.status_code)