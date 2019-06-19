#!/usr/bin/env python
# -*- coding: utf-8 -*-

# forwarder.py - forwards IoT sensor data from MQTT to InfluxDB
#
# Copyright (C) 2016 Michael Haas <haas@computerlinguist.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import argparse
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import json
import re
import logging
import sys
import requests.exceptions
import ConfigParser

class MessageStore(object):

    def store_msg(self, node_name, measurement_name, value):
        raise NotImplementedError()

class InfluxStore(MessageStore):

    logger = logging.getLogger("forwarder.InfluxStore")

    def __init__(self, host, port, username, password_file, database):
        password = open(password_file).read().strip()
        self.influx_client = InfluxDBClient(
            host=host, port=port, username=username, password=password, database=database)
        self.influx_client.create_database('sensors')


    def store_msg(self, tag, measurement_name, data):
        if not isinstance(data, dict):
            raise ValueError('data must be given as dict!')
        influx_msg = {
            'measurement': measurement_name,
            'tags': tag,
            'fields': data
        }
        self.logger.debug("Writing InfluxDB point: %s", influx_msg)
        try:
            pass
            self.influx_client.write_points([influx_msg])
        except requests.exceptions.ConnectionError as e:
            self.logger.exception(e)

class MessageSource(object):

    def register_store(self, store):
        if not hasattr(self, '_stores'):
            self._stores = []
        self._stores.append(store)

    @property
    def stores(self):
        # return copy
        return list(self._stores)


class MQTTSource(MessageSource):

    logger = logging.getLogger("forwarder.MQTTSource")

    def __init__(self, host, port, node_names, configobj):
        self.host = host
        self.port = port
        self.cfg = configobj
        self.node_names = node_names
        self._setup_handlers()

    def _setup_handlers(self):
        self.client = mqtt.Client()

        def on_connect(client, userdata, flags, rc):
            self.logger.info("Connected with result code  %s", rc)
            # subscribe to /node_name/wildcard
            for node_name in self.node_names:
                topic = "{node_name}/#".format(node_name=node_name)
                self.logger.info(
                    "Subscribing to topic %s for node_name %s", topic, node_name)
                client.subscribe(topic)

        def on_message(client, userdata, msg):
            self.logger.debug(
                "Received MQTT message for topic %s with payload %s", msg.topic, msg.payload)
            print(msg.topic)
            if(self.cfg.has_section(msg.topic)):
              print("got config")
#              itmcfg=self.cfg.opt(msg.topic)
#              print(itmcfg)
#measurement = vind-humidity
#tags = vind,humidity
#format = float

              value = msg.payload
              if ((self.cfg.has_option(msg.topic, 'format')) & (self.cfg.get(msg.topic, 'format')=='float')):
                try:
                  value = float(value)
                except ValueError:
                  pass
              elif ((self.cfg.has_option(msg.topic, 'format')) & (self.cfg.get(msg.topic, 'format')=='int')):
                try:
                  value = int(value)
                except ValueError:
                  pass
              elif ((self.cfg.has_option(msg.topic, 'format')) & (self.cfg.get(msg.topic, 'format')=='str')):
                  pass
              else :
                self.logger.warning("Type missing for ", msg.topic)
              print(self.cfg.get(msg.topic, 'tags'))
              if (self.cfg.has_option(msg.topic, 'tags')):
#                try:
                tags=json.loads(self.cfg.get(msg.topic, 'tags'))
#                ags=json.loads('{ "name":"John", "age":30, "city":"New York"}')
#                except:
#                  pass
                print (tags)
              else:
                tags=None

              stored_message = {'value': value}

              for store in self.stores:
                  store.store_msg(tags, msg.topic, stored_message)

        self.client.on_connect = on_connect
        self.client.on_message = on_message

    def start(self):
        self.client.connect(self.host, self.port)
        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        self.client.loop_forever()


def main():
    cfgfile='pjofwd.conf'
    config = ConfigParser.ConfigParser({'mqtt-port':'1883','influx-port':'8086'})
    config.read(cfgfile)
    print(config.sections())

    try:
      mqtthosta=config.get('CONFIG', 'mqtt-host')
      mqtthostb=config.get('CONFIG', 'mqtt-port')
      mqtthostc=config.get('CONFIG', 'influx-host')
      mqtthostd=config.get('CONFIG', 'influx-port')
      mqtthoste=config.get('CONFIG', 'mqtt-topic')
      mqtthostf=config.get('CONFIG', 'debug-level')
    except:
      logging.exception('Config incorrect')

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
	

    print(config.sections())
    store = InfluxStore(host='127.0.0.1', port='8086',
            username='wthr', password_file='pwd.txt', database='weathersys')
    source = MQTTSource(host='127.0.0.1',
                        port='1883', node_names=['sensors'], configobj=config)
    source.register_store(store)
    source.start()

if __name__ == '__main__':
    main()
