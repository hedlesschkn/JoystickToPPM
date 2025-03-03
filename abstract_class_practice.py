from math import pi

class Circle:
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return pi * self.radius ** 2

class Rectangle:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

def total_area(shapes) -> float:
    return sum(shape.area() for shape in shapes)

shapes = [
    Circle(5),
    Rectangle(4, 6)
]

print("circle area:", Circle(5).area())
print("circle area:", Rectangle(4,6).area())
total_temp = (Circle(5).area())+(Rectangle(4,6).area())
print("temp area:", total_temp)

print("Total Area:", total_area(shapes))