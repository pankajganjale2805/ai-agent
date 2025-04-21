from setup.next_project import setup_next_project
from routes.create_routes import generate_next_pages


def main():
    setup_next_project()
    generate_next_pages()


if __name__ == "__main__":
    main()
