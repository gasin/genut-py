from genut_py import GenUT


class User:
    def __repr__(self):
        return f"User(name={self.name.__repr__()}, age={self.age.__repr__()})"

    def __init__(self, name, age):
        self.name = name
        self.age = age

    @GenUT
    def is_adult(self):
        if self.age >= 20:
            return f"{self.name} is adult"
        return f"{self.name} is child"


user = User(name="John", age=19)
user.is_adult()
user2 = User(name="Tom", age=25)
user2.is_adult()
