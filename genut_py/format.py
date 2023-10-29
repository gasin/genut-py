def snake_to_camel(snake_str: str) -> str:
    """Convert snake case to camel case

    Args:
        snake_str: Snake case string

    Returns:
        A string converted to camel case

    """

    def word_to_camel(word: str) -> str:
        if word == "":
            return ""
        return word[0].upper() + word[1:]

    return "".join(map(word_to_camel, snake_str.split("_")))


def camel_to_snake(camel_str: str) -> str:
    """Convert camel case to snake case

    Args:
        camel_str: Camel case string

    Returns:
        A string converted to snake case

    """

    snake_str = ""
    for i, c in enumerate(camel_str):
        if i > 0 and c.isupper():
            snake_str += "_"
        snake_str += c.lower()

    return snake_str
