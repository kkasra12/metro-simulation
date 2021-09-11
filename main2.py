import random
from typing import Dict

import vpython
from vpython import color

# import configs
# import utilities
from configs import COLORS, FINAL_BOUNDING_RECT, STATION_SIZE, NUMBER_OF_TOTAL_PASSENGER
from metronet import metronet
from utilities import Station, Line, find_bounding_rect, Passenger, Train

# read all stations

for line_number, station_name, station_position in metronet:
    if line_number not in Line.all_lines:
        current_line = Line(line_number)
        Line.all_lines.update({line_number: current_line})
    else:
        current_line = Line.all_lines[line_number]
    if station_name in Station.all_stations:
        Station.all_stations[station_name].add_line(current_line)
    else:
        Station.all_stations.update({station_name: Station(station_name, station_position, lines=[current_line])})

# rescale
initial_bounding_rect = find_bounding_rect(list(Station.all_stations.values()))
for _, station in Station.all_stations.items():
    station.rescale(*initial_bounding_rect, *FINAL_BOUNDING_RECT)
##
# vpython.canvas(width=5000,heights=20)
t = FINAL_BOUNDING_RECT[1] - FINAL_BOUNDING_RECT[0]
vpython.scene.center = t / 2
vpython.scene.range = max(t.x, t.y, t.z) / 2
###
vpython.scene.title = "Created by Kasra"
vpython.scene.width = 1000
vpython.scene.height = 600
###
curves = {line_number: vpython.curve(pos=[station.position for station in Line.all_lines[line_number].stations],
                                     color=COLORS.get(line_number, color.purple)) for line_number in Line.all_lines}

spheres = {station_number: vpython.sphere(pos=station.position, color=color.yellow, radius=STATION_SIZE) for
           station_number, station in Station.all_stations.items()}

passengers: Dict[str, Passenger] = {
    f"pass_{i}": Passenger(location=random.choice(list(Station.all_stations.values()))) for i in
    range(NUMBER_OF_TOTAL_PASSENGER)}

# for s in Station.all_stations:
#     print(s, [passenger for passenger in passengers.values() if passenger.location.name == s])

##
for line in Line.all_lines.values():
    Train.all_train.update({line.number: Train(line=line, name=f"train_{line.number}")})
while 1:
    for train in Train.all_train.values():
        train.update()
    # print(test_train.pos)
    vpython.rate(30)
