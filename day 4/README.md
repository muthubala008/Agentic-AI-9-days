# College Academic Assistant Agent

## 1. Project Overview

The College Academic Assistant Agent is an AI-powered academic information assistant.

It allows students to ask questions using natural language. A Gemini-based Supervisor Agent analyzes the query and selects the appropriate tool to retrieve information from a local academic repository.

The system currently supports:

- Course information
- Course prerequisites
- Course credits
- Course descriptions
- Learning resources
- Tutorials
- Documentation
- Study materials

---

## 2. Problem Statement

Students often need to search different sources to find course information and learning resources.

This project provides a conversational academic assistant that can understand natural-language questions and automatically select the appropriate tool to retrieve information from a structured academic database.

Example queries:

- "What is the prerequisite for Machine Learning?"
- "Tell me about Data Structures."
- "Give me resources to learn Python."
- "What resources are available for NumPy?"

---

## 3. Objectives

The main objectives are:

1. Accept natural-language academic queries.
2. Use Gemini as the Supervisor Agent.
3. Select the appropriate tool based on the query.
4. Retrieve information from SQLite.
5. Return a concise natural-language response.
6. Demonstrate tool calling and agent-based architecture.

---

## 4. Architecture

```text
                         USER
                           |
                           v
                    +-------------+
                    |   FastAPI   |
                    |    /ask     |
                    +------+------+
                           |
                           v
                 +-------------------+
                 | Gemini Supervisor |
                 |      Agent        |
                 +---------+---------+
                           |
                 +---------+---------+
                 |                   |
                 v                   v
        +----------------+   +----------------------+
        |  Course Tool   |   |    Resource Tool    |
        |                |   |                      |
        | get_course_    |   | search_study_        |
        | information()  |   | resources()          |
        +-------+--------+   +----------+-----------+
                |                       |
                +-----------+-----------+
                            |
                            v
                  +-------------------+
                  | Repository Layer  |
                  |   database.py     |
                  +---------+---------+
                            |
                            v
                  +-------------------+
                  |      SQLite       |
                  |    academic.db    |
                  +-------------------+