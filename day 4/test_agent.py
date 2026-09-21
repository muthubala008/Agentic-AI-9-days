from app.agent import ask_agent


def main():

    print("=" * 60)
    print("COLLEGE ACADEMIC ASSISTANT")
    print("=" * 60)

    while True:

        query = input("\nYou: ")

        if query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        try:
            answer = ask_agent(query)

            print("\nAgent:", answer)

        except Exception as e:
            print("\nError:", e)


if __name__ == "__main__":
    main()