from vpython import color, vector

COLORS = {1: color.red, 2: color.magenta, 5: color.orange, 6: color.blue}
FINAL_BOUNDING_RECT = (vector(0, 0, 0), vector(800, 600, 0))

METRO_SIZE = 10
METRO_SPEED = 0.5
METROS_CAPACITY = 100

WAITING_TIME_MEAN = 15
WAITING_TIME_TOL = 5
STATION_SIZE = 3

PASSENGER_GETTING0F_PROB = 0.2
PASSENGER_LEFT_THE_SYSTEM_PROB = 0.2
PASSENGER_BOARD_PROB = 0.8
# the probability of doing nothing is: 1 - PASSENGER_LEFT_THE_SYSTEM_PROB - PASSENGER_GETTING0F_PROB
# doing nothing means stay in train

NUMBER_OF_TOTAL_PASSENGER = 2000