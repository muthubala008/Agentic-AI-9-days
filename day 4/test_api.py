import requests


url = "http://127.0.0.1:8000/ask"


queries = [
    "What is the prerequisite for Machine Learning?",
    "Give me resources to learn Python."
]


for query in queries:

    response = requests.post(
        url,
        json={
            "query": query
        }
    )

    print("\n" + "=" * 60)
    print("QUESTION:")
    print(query)

    print("\nRESPONSE:")
    print(response.json())