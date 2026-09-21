from app.repository.database import get_course


def get_course_information(course_name: str) -> dict:
    """
    Get academic information about a college course.

    Use this tool when the user asks about:
    - course information
    - course credits
    - prerequisites
    - course description
    - course code
    """

    course = get_course(course_name)

    if course is None:
        return {
            "success": False,
            "message": f"No course named '{course_name}' was found."
        }

    return {
        "success": True,
        "course": course
    }