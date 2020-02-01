import json
import random


def random_mass():
    return random.random() * 3_000


# potato density is at most 1.5 g/ml
# 1/1.5 = 0.6666
# 0.66 * 3,000 = 2000
def random_volume():
    return random.random() * 2_000


def random_introduced():
    return {
        "when": random.randint(1, 1e10),
        "where": random.randint(0, 50)
    }


def get_density(mass, volume):
    return mass / volume


def get_variety(max_length, max_width, density, image):
    pass


def get_size(mass, volume, max_length, max_width):
    pass


def get_grade(density, variety, size, image, heightmap, when_introduced):
    pass
