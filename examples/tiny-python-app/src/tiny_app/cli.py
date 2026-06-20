from __future__ import annotations


def greeting(name: str = "world") -> str:
    return f"hello, {name}"


def main() -> None:
    print(greeting())


if __name__ == "__main__":
    main()
