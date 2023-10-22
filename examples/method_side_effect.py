from genut_py import GenUT


class User:
    def __repr__(self):
        return f"User(name={self.name.__repr__()}, age={self.age.__repr__()})"

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age

    def __init__(self, name, age):
        self.name = name
        self.age = age

    @GenUT
    def update_age(self, age):
        if age == self.age:
            return
        self.age = age


user = User(name="John", age=19)
user.update_age(20)
