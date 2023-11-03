import dataclasses

from genut_py import GenUT


@dataclasses.dataclass(slots=True)
class User:
    name: str
    age: int

    @GenUT
    def update_age(self, age):
        if age == self.age:
            return self.age
        self.age = age
        return self.age


user = User(name="John", age=19)
user.update_age(20)
user.update_age(20)
