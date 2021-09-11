import random
import re
from typing import List, Tuple, Union, Dict

import vpython

from configs import WAITING_TIME_MEAN, WAITING_TIME_TOL, METROS_CAPACITY, METRO_SPEED, PASSENGER_GETTING0F_PROB, \
    PASSENGER_LEFT_THE_SYSTEM_PROB, METRO_SIZE, PASSENGER_BOARD_PROB


class Station:
    passengers: List['Passenger']
    position: vpython.vector

    all_stations: Dict[str, 'Station'] = {}

    def __init__(self, name: str, position: Union[str, vpython.vector], lines: List['Line'] = None):
        if lines is None:
            lines = []
        self.name = name
        if isinstance(position, str):
            self.position = vpython.vector(*list(self.geolocation_to_decimal(position)), 0)
        else:
            self.position = position
        self.lines = []
        for line in lines:
            self.add_line(line)
        self.waiting_time = WAITING_TIME_MEAN + random.randint(-WAITING_TIME_TOL,
                                                               WAITING_TIME_TOL)
        self.passengers = []

    @staticmethod
    def geolocation_to_tuple(degree_str):
        matched = re.match(r"(\d+)°(\d+)′(\d+)″[EN]", degree_str)
        if matched is None:
            raise ValueError(f"{degree_str} is not valid location")
        ans = tuple(int(matched.group(i)) for i in [1, 2, 3])
        if not (0 <= ans[0] <= 360 and 0 <= ans[1] <= 60 and 0 <= ans[2] <= 60):
            raise ValueError(f"entries not in range, {ans}")
        return ans

    @classmethod
    def geolocation_to_decimal(cls, position: str):
        for i in position.split():
            g, m, s = cls.geolocation_to_tuple(i)
            yield int((g + m / 60 + s / 3600) * 1e6)

    def add_line(self, line: 'Line'):
        if line not in self.lines:
            self.lines.append(line)
        line.add_station(self)

    def draw_station(self, curve: vpython.curve):
        curve.append(self.position)

    def rescale(self, initial_min_vector: vpython.vector, initial_max_vector: vpython.vector,
                final_min_vector: vpython.vector,
                final_max_vector: vpython.vector, inplace=True):
        new_x = (self.position.x - initial_min_vector.x) * (final_max_vector.x - final_min_vector.x) / (
                initial_max_vector.x - initial_min_vector.x) + final_min_vector.x
        new_y = (self.position.y - initial_min_vector.y) * (final_max_vector.y - final_min_vector.y) / (
                initial_max_vector.y - initial_min_vector.y) + final_min_vector.y
        if inplace:
            self.position.x = new_x
            self.position.y = new_y
        else:
            return self.__class__(name=self.name, position=vpython.vector(new_x, new_y, 0), lines=self.lines)

    def add_passenger(self, passenger: 'Passenger'):
        passenger.location = self
        self.passengers.append(passenger)


def find_bounding_rect(all_stations: List[Station]) -> Tuple[vpython.vector, vpython.vector]:
    min_x = all_stations[0].position.x
    min_y = all_stations[0].position.y
    max_x = all_stations[0].position.x
    max_y = all_stations[0].position.y
    for station in all_stations:
        pos = station.position
        min_x = min(min_x, pos.x)
        min_y = min(min_y, pos.y)
        max_x = max(max_x, pos.x)
        max_y = max(max_y, pos.y)
    return vpython.vector(min_x, min_y, 0), vpython.vector(max_x, max_y, 0)


class Line:
    all_lines: Dict[int, 'Line'] = {}

    def __init__(self, number: int, stations: List[Station] = None):
        if stations is None:
            stations = []
        self.number = number
        self.stations = stations

    def add_station(self, station: Station):
        if station not in self.stations:
            self.stations.append(station)

    def __repr__(self):
        return f"Line(Number: {self.number},station_name: {[station.name for station in self.stations]}"


class Train:
    distance_between_two_stations: float
    direction: vpython.vector
    passengers: List['Passenger']

    all_train: Dict[int, 'Train'] = {}

    def __init__(self, line: Line, name: str, capacity: int = None):
        self.line = line
        self.name = name
        self.capacity = capacity or METROS_CAPACITY
        self.passengers = []
        self.stations_queue = line.stations.copy()
        self.pos = line.stations[0].position
        self.speed = METRO_SPEED
        self.is_moving = False
        self.frames_remained_to_stay = -1
        '''
        if len(location)==1 then the train is in the station
        if len(location)==2 then the train is in the way to next station        
        '''
        self.__bigger_cylinder = vpython.cylinder(radius=5, color=vpython.color.green)
        self.__smaller_cylinder = vpython.cylinder(radius=5, color=vpython.color.magenta)
        # self.arrow = vpython.arrow(pos=self.pos, axis=self.stations_queue[1].position - self.pos)
        self.movement_initialization()

    def movement_initialization(self):
        self.direction = self.stations_queue[1].position - self.stations_queue[0].position
        self.direction.mag = 1
        self.distance_between_two_stations = vpython.mag(
            self.stations_queue[1].position - self.stations_queue[0].position)
        self.is_moving = True

    def update_pos(self):
        if not self.is_moving:
            raise RuntimeError("in update_pos, self.is_moving cannot be True.\n"
                               "this is an internal error please report this error")
        else:
            self.pos += self.direction * self.speed
            self.__smaller_cylinder.pos = self.pos
            self.__bigger_cylinder.pos = self.pos

            self.__bigger_cylinder.axis = self.direction * METRO_SIZE
            self.__smaller_cylinder.axis = self.direction * len(self.passengers) / self.capacity * METRO_SIZE
            distance_from_previous_station = vpython.mag(self.stations_queue[0].position - self.pos)
            # vpython.arrow(pos=self.pos, axis=self.stations_queue[0].position - self.pos)
            # self.arrow.pos = self.pos
            # self.arrow.axis = self.stations_queue[1].position - self.pos
            if distance_from_previous_station >= self.distance_between_two_stations:
                # this means we reached next station
                self.is_moving = False
                self.stations_queue.pop(0)
                if len(self.stations_queue) == 1:
                    self.stations_queue.extend(self.line.stations[-2::-1])
                self.frames_remained_to_stay = 0

    def update(self):
        if self.is_moving:
            self.update_pos()
        else:
            if self.frames_remained_to_stay == 0:
                print(f"number of passengers in station {self.stations_queue[0].name} "
                      f"is {len(self.stations_queue[0].passengers)}")
                self.passengers = [passenger for passenger in self.passengers if not passenger.update()]
                this_station = self.stations_queue[0]
                this_station.passengers = [passenger for passenger in this_station.passengers if
                                           not passenger.update(waiting_train=self)]
                print(len(self.passengers))
            self.frames_remained_to_stay += 1
            if self.frames_remained_to_stay >= self.stations_queue[0].waiting_time:
                self.movement_initialization()

    def add_passenger(self, passenger: 'Passenger'):
        if self.capacity - len(self.passengers) >= 1:
            passenger.location = self
            self.passengers.append(passenger)
            return True
        return False


class Passenger:
    location: Union[Train, Station]

    def __init__(self, location: Union[Train, Station]):
        location.add_passenger(self)

    def update(self, waiting_train: Train = None):
        """
        if this function returns true it mean the passenger moved, otherwise passenger holds its position
        :return: True or False
        """
        t = random.random()
        if isinstance(self.location, Train):
            if t < PASSENGER_GETTING0F_PROB:
                # here passenger will go and stay in station
                self.location.stations_queue[0].add_passenger(self)
                return True
            if t < PASSENGER_GETTING0F_PROB + PASSENGER_LEFT_THE_SYSTEM_PROB:
                # here passenger lefts the system, so we must create new passenger in other station
                # instead of making new passenger i can simply teleport this passenger to other place
                random.choice(list(Station.all_stations.values())).add_passenger(self)
                return True
            return False
        elif isinstance(self.location, Station):
            if waiting_train is None:
                raise ValueError("waiting_train must not be empty in here\n"
                                 "this is an internal error please report this")
            if t < PASSENGER_BOARD_PROB:
                return waiting_train.add_passenger(self)
            return False
