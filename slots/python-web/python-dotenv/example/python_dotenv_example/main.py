import os

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    greeting = os.environ.get("GREETING", "hello")
    name = os.environ.get("NAME", "world")
    print(f"{greeting}, {name}")


if __name__ == "__main__":
    main()
