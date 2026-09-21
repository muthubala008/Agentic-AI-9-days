from app.tools.course_tool import get_course_information
from app.tools.resource_tool import search_study_resources


print("\n--- TOOL 1 TEST ---")

result = get_course_information("Machine Learning")

print(result)


print("\n--- TOOL 2 TEST ---")

result = search_study_resources("Python")

print(result)