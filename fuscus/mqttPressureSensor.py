#!/usr/bin/env python3
"""Threaded, filtered class for reading DS18B20 temperature sensors."""

#
# Copyright 2015 Andrew Errington
# Copyright 2020 Henrik Halvorsen
#
# This file is part of BrewPi.
# 
# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.
#

import FilterCascaded

import time
import logging

import paho.mqtt.client as mqtt


# tempSensor class for BrewPi
# Subclassed from DS18B20, which is a general purpose threaded class
# for reading DS18B20 one-wire temperature sensors.

# This class adds filtering and other functions to the sensor.

class sensor():
    def __init__(self, broker, topic, calibrationOffset=0.0):

        self.topic = topic
        self.temperature = None
        self.deviceID = -1

        if self.topic is not None:
            self._connection = mqtt.Client()
            self._connection.connect(str(broker))
            self._connection.message_callback_add(self.topic, self.topicUpdate)
            result, self.mid = self._connection.subscribe(topic, 0)
            self._connection.loop_start()

        # An indication of how stale the data is in the filters
        # Each time a read fails, this value is incremented.
        # It's used to reset the filters after a large enough disconnect
        # delay, and on the first init.

        self.failedReadCount = 255
        self.updateCounter = 64

        self.fastFilter = FilterCascaded.CascadedFilter()
        self.slowFilter = FilterCascaded.CascadedFilter()
        self.slopeFilter = FilterCascaded.CascadedFilter()
        self.prevOutputForSlope = None

        time.sleep(1)  # Wait for at least one reading to be ready.

    def stop(self):
        self.join()

    def isConnected(self):
        return self.topic is not None

    def init(self):
        logging.debug("tempsensor::init - begin %d", self.failedReadCount)
        # if (_sensor && _sensor->init() && failedReadCount>60) {
        if (self.failedReadCount > 60):
            temp = self.temperature
            if (temp is not None):
                logging.debug("initializing filters with value %d", temp)
                self.fastFilter.init(temp)
                self.slowFilter.init(temp)
                self.slopeFilter.init(0)
                self.prevOutputForSlope = self.slowFilter.readOutput()
                self.failedReadCount = 0

    def topicUpdate(self, client, userdata, message):
        # if (!_sensor || (temp=_sensor->read())==TEMP_SENSOR_DISCONNECTED) {
        print("Update for %s: %s" % (self.topic, message.payload.decode("utf-8")))
        self.temperature = float(message.payload.decode("utf-8"))
        
    def join(self):
        if self.topic is not None:
            self._connection.unsubscribe(self.topic)
            self._connection.loop_stop()
            self._connection.disconnect()
        return

    def update(self):
        temp = self.temperature
        if (temp is None):
            if (self.failedReadCount < 255):  # limit
                self.failedReadCount += 1
            return

        self.fastFilter.add(temp)
        self.slowFilter.add(temp)
        # update slope filter every 3 samples.
        # averaged differences will give the slope. Use the slow filter as input
        self.updateCounter -= 1
        # prevents an influence for the startup inaccuracy.
        if (self.updateCounter == 4):
            # only happens once after startup.
            self.prevOutputForSlope = self.slowFilter.readOutput()

        if (self.updateCounter <= 0):
            slowFilterOutput = self.slowFilter.readOutput()
            diff = slowFilterOutput - self.prevOutputForSlope
            # diff_upper = diff >> 16
            # if(diff_upper > 27){ // limit to prevent overflow INT_MAX/1200 = 27.14
            #	diff = (27l << 16);
            # }
            # else if(diff_upper < -27){
            #	diff = (-27l << 16);
            # }

            self.slopeFilter.add(200 * diff)  # Multiply by 1200 (1h/4s), shift to single precision
            self.prevOutputForSlope = slowFilterOutput
            self.updateCounter = 3


    def readFastFiltered(self):
        return self.fastFilter.readOutput()  # return most recent unfiltered value

    def readSlowFiltered(self):
        return self.slowFilter.readOutput()  # return most recent unfiltered value

    def readSlope(self):
        """Return slope per hour."""
        return self.slopeFilter.readOutput()

    def detectPosPeak(self):
        return self.slowFilter.detectPosPeak()

    def detectNegPeak(self):
        return self.slowFilter.detectNegPeak()

    def setFastFilterCoefficients(self, b):
        self.fastFilter.setCoefficients(b)

    def setSlowFilterCoefficients(self, b):
        self.slowFilter.setCoefficients(b)

    def setSlopeFilterCoefficients(self, b):
        self.slopeFilter.setCoefficients(b)

    def hasSlowFilter(self):
        return True

    def hasFastFilter(self):
        return True

    def hasSlopeFilter(self):
        return True
