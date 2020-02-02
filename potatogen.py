#! /usr/bin/env python3
import hashlib
import random


def random_choice(l):
    return l[random.randint(0, len(l) - 1)]


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


def random_3d():
    return {
        "image": "(base64)",
        "heightmap": "(base64)"
    }


def get_density(mass, volume):
    return mass / volume


def get_variety(max_length, max_width, density, image):
    varieties = ["red", "white", "yellow", "russet", "fingerling",
                 "queen_anne", "sweet"]
    return random_choice(varieties)


def get_size(mass, volume, max_length, max_width):
    sizes = ["chef", "A", "B", "creamer", "small", "medium", "large"]
    return random_choice(sizes)


def get_grade(density, variety, size, image, heightmap, when_introduced):
    grades = ["1", "C", "2", "3"]
    return random_choice(grades)


def random_evident():
    return {
        "mass": random_mass(),
        "volume": random_volume(),
        "introduced": random_introduced(),
        "3d": random_3d()
    }


def random_emergent(evident):
    return {
        "density": get_density(evident['mass'], evident['volume']),
        "variety": get_variety(0, 0, 0, 0),
        "size": get_size(0, 0, 0, 0),
        "grade": get_grade(0, 0, 0, 0, 0, 0),
    }


def sha256_dict(d):
    from io import BytesIO
    buf = BytesIO()
    for k in sorted(d.keys()):
        if isinstance(d[k], dict):
            buf.write( bytes(
                "\n".join(str(v) for v in sorted(d[k].keys())),
                "utf8"
            ))
        elif isinstance(d[k], list):
            buf.write(bytes(
                "\n".join(str(v) for v in d[k]),
                "utf8"
            ))
        else:
            # print(d[k])
            buf.write(bytes(
                str(d[k]) + "\n",
                "utf8"
            ))

    return hashlib.sha256( buf.getvalue() ).hexdigest()


def random_potato():
    evident = random_evident()
    emergent = random_emergent(evident)
    sha_ev = sha256_dict(evident)
    sha_em = sha256_dict(emergent)

    uid = hashlib.sha256(bytes(sha_ev + "\n" + sha_em, "ascii")).hexdigest()
    return {
        "history": [],
        "id": uid,
        "evident": evident,
        "emergent": emergent
    }


def checksum_potato(p):
    pass


if __name__ == '__main__':
    import json
    print(json.dumps([random_potato() for i in range(10)]))
