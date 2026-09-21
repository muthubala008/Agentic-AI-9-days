from app.repository.database import search_resources


def search_study_resources(topic: str) -> dict:
    """
    Search for learning resources about an academic topic.

    Use this tool when the user asks for:
    - tutorials
    - books
    - documentation
    - courses
    - study resources
    - learning materials
    """

    resources = search_resources(topic)

    if not resources:
        return {
            "success": False,
            "message": f"No study resources were found for '{topic}'."
        }

    return {
        "success": True,
        "topic": topic,
        "resources": resources
    }