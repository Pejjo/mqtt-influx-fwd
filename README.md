# IoT MQTT to InfluxDB forwarder #

This tool forwards IoT sensor data from an MQTT broker to an InfluxDB instance.

## MQTT topic structure ##

The topic structure should be path-like, where the first element in the hierarchy contains
the name of the sensor node. Below the node name, the individual measurements are published
as leaf nodes. Each sensor node can have multiple sensors.

The tool takes a list of node names and will auto-publish all measurements found
below these node names. Any measurements which look numeric will be converted to
a float.

### Example MQTT topic structure ###

A simple weather station with some sensors may publish its data like this:

    /weather/uv: 0 (UV indev)
    /weather/temp: 18.80 (Â°C)
    /weather/pressure: 1010.77 (hPa)
    /weather/bat: 4.55 (V)

Here, 'weather' is the node name and 'humidity', 'light' and 'temperature' are
measurement names. 0, 18.80, 1010.88 and 4.55 are measurement values. The units
are not transmitted, so any consumer of the data has to know how to interpret
the raw values.

## Translation to InfluxDB data structure ##

The MQTT topic structure and measurement values are mapped in a config file.
First part is general:
[CONFIG]
influx-host = 127.0.0.1
inlux-port = xxxx
mqtt-host = 127.0.0.1
mqtt-port = xxxx
mqtt-topic = sensors/,dics/ 
debug-level= DEBUG

For each mqtt-influx pair, a section is added 
[mqtt/topic]
measurement = maren
tags = {"location":"Maren","measurement":"lufttemperatur","sensor":"temp"}
format = float #Can also be int or str

### Example InfluxDB query ###

    select value from bat;
    select value from bat where sensor_node = 'weather' limit 10;
    select value from bat,uv,temp,pressure limit 20; 

The data stored in InfluxDB via this forwarder are easily visualized with [Grafana](http://grafana.org/)

## License ##

See the LICENSE file.

## Versioning ##

[Semantic Versioning](http://www.semver.org)
