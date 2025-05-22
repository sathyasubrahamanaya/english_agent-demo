from typing_extensions import DefaultDict
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from google.genai import types
from agno.models.google import Gemini
from agno.storage.sqlite import SqliteStorage
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from textwrap import dedent


# Configuration for content generation
generate_content_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0),
    response_mime_type="text/plain",
)


memory = Memory(db=SqliteMemoryDb(table_name="agent_memories", db_file="tmp/memory.db"))

# Define constants
TOPIC_NAME = "Grammar"
ENGLISH_SUBTOPICS = [
    "sentence patterns", "noun phrases", "verb phrases", "tenses", "parts of speech",
    "subject-predicate", "phrases and clauses", "types of sentences", "articles", "determiners"
]
NATIVE_LANGUAGE = "Malayalam"
LANG_CODE = "Mal"



TEACHING_MODES = ("EXPLAIN", "EXAMINE")
SUBTOPIC_PERFORMANCE_STATE = ("BEGINNER", "AVERAGE", "GOOD", "BETTER", "BEST", "EXPERT")

# Initial state for the user
init_state = {
    "current_topic": TOPIC_NAME,
    "sub_topics": ENGLISH_SUBTOPICS,
    "current_sub_topic": ENGLISH_SUBTOPICS[0],
    "sub_topic_index": 0,
    "teaching_modes": TEACHING_MODES,
    "current_teaching_mode": TEACHING_MODES[0],
    "exercise_rounds_count": 0,
    "all_performance_level": SUBTOPIC_PERFORMANCE_STATE,
    "level": SUBTOPIC_PERFORMANCE_STATE[0],
    "current_performance_score": 0
}

# Model initialization (replace with your API keys)
GROQ_API_KEY = "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"
GOOGLE_API_KEY = "AIzaSyBzob_1guHO-eK_4cWyxI_toBHw8XVM338"
llma4_mavrick_id = "meta-llama/llama-4-maverick-17b-128e-instruct"
model = Groq(id = llma4_mavrick_id,api_key=GROQ_API_KEY)
gemini_model = Gemini(id="gemini-2.5-flash-preview-04-17",api_key=GOOGLE_API_KEY,generation_config=generate_content_config)

# Tools for teaching mode and state management
def examine_mode(agent: Agent) -> str:
    """Switch to EXAMINE mode for testing the user's knowledge."""
    print("Switching to EXAMINE mode.")
    agent.session_state["current_teaching_mode"] = "EXAMINE"
    return "Teaching mode switched to EXAMINE."

def explain_mode(agent: Agent) -> str:
    """Switch to EXPLAIN mode for teaching concepts."""
    print("Switching to EXPLAIN mode.")
    agent.session_state["current_teaching_mode"] = "EXPLAIN"
    return "Teaching mode switched to EXPLAIN."

def next_sub_topic(agent: Agent) -> str:
    """Advance to the next sub-topic in the list."""
    print("Moving to the next sub-topic.")
    sub_topics = agent.session_state["sub_topics"]
    current_index = agent.session_state["sub_topic_index"]
    if current_index < len(sub_topics) - 1:
        agent.session_state["sub_topic_index"] += 1
        agent.session_state["current_sub_topic"] = sub_topics[agent.session_state["sub_topic_index"]]
    else:
        agent.session_state["current_sub_topic"] = "All sub-topics completed."
    return f"Moved to sub-topic: {agent.session_state['current_sub_topic']}"

def update_exercise_rounds_count(agent: Agent) -> str:
    """Increment the exercise rounds counter."""
    print("Updating exercise rounds count.")
    agent.session_state["exercise_rounds_count"] += 1
    return f"Exercise rounds count updated to {agent.session_state['exercise_rounds_count']}."

def update_score(agent: Agent, score: float) -> str:
    """Update the user's performance score."""
    print("Updating score.")
    agent.session_state["current_performance_score"] += score
    return f"Score updated to {agent.session_state['current_performance_score']}."

def reset_exercise_count(agent: Agent) -> str:
    """Reset the exercise rounds counter to 0."""
    print("Resetting exercise rounds count.")
    agent.session_state["exercise_rounds_count"] = 0
    return f"Exercise rounds count reset to {agent.session_state['exercise_rounds_count']}."

def reset_score(agent: Agent) -> str:
    """Reset the user's score to 0."""
    print("Resetting score.")
    agent.session_state["current_performance_score"] = 0
    return f"Score reset to {agent.session_state['current_performance_score']}."

def reset_level(agent: Agent) -> str:

    """Reset the user's performance level to BEGINNER."""
    print("Resetting level.")
    agent.session_state["level"] = SUBTOPIC_PERFORMANCE_STATE[0]
    return f"Level reset to {agent.session_state['level']}."
def update_understanding_level(agent: Agent, new_level: str) -> str:
    """Update the user's understanding level."""
    print(f"Updating understanding level to {new_level}.")
    agent.session_state["level"] = new_level
    return f"Understanding level updated to {new_level}."
# Agent initialization with tuned prompts
agent = Agent(
    model=gemini_model,
    name="Manisha",
    role="English Trainer",
    add_history_to_messages=True,
    user_id="user1",
    storage=SqliteStorage(table_name="agent_sessions", db_file="tmp/memory.db"),
    enable_user_memories=True,
    enable_session_summaries=True,
    session_id="user1_session1",
    num_history_responses=10,
    add_session_summary_references=True,
    session_state=init_state,
    goal=f"Teach {TOPIC_NAME} to help the user speak English fluently.",
    description=dedent("""You are Manisha, a friendly English coach for {NATIVE_LANGUAGE}-speaking beginners.
    Your user, {user_name}, is new to English. Respond the explantion in {NATIVE_LANGUAGE} language.
    (script: {LANG_CODE}) for explanation.engage them with their {NATIVE_LANGUAGE}. Make learning fun and engaging!"""),

    instructions=dedent("""
    ### Teaching Workflow for {user_name}
    Based on the user's state: the user name is {user_name}
    the (current_topic) is :{current_topic}
    the (sub topics) {sub_topics}
    current_sub_topic is :: {current_sub_topic}
    the current sub_topic_index :: {sub_topic_index}
    Teaching Modes are {teaching_modes}
    the current_teaching_mode is:: {current_teaching_mode}
    current excercise round count:: {exercise_rounds_count}
    Available performance level are {all_performance_level}
    the current performance level is {level}
    the current performance score is {current_performance_score}
    the current user id {current_user_id}
    the current session id {current_session_id}

    1. **Start with the Current Sub-Topic**: {current_sub_topic}
       - Check the {current_teaching_mode} and follow the steps below.

    2. **EXPLAIN Mode**:
       - Explain {current_sub_topic} in  with NATIVE_LANGUAGE.
       - if they ask doubt solve the doubt and give a similar example to it.stay with the topic always
       - Use examples relatable to NATIVE_LANGUAGE culture (e.g., daily activities, food).
       - Apply the **teach-back method**: Ask the user to explain the concept back to you also give some examples.
       - after teachback always give 2-3 excercises update the level by calling update_understanding_level tool with options availabe with {all_performance_level}
       - If they struggle, repeat with more examples.
         If they succeed by checking level of understanding in {level} then switch to `examine_mode`.
         else repeat the step 2

    3. **EXAMINE Mode**:
       - Ask up to 5 questions on {current_sub_topic}.
       - After each question:
         - Correct answer: Add 1 to {current_performance_score} via `update_score` tool.
         - Partial answer: Add 0.5, correct it, and proceed.
         - Doubt: Answer it with an example, then move on.
       - Track rounds with `update_exercise_rounds_count` only if EXAMINE mode by checking {current_teaching_mode}.

       - After completing the rounds, ask: "Did you understand {current_sub_topic}?" if
         - Yes: Offer "more explanation" (call `explain_mode`) or "more exercises" (stay in `EXAMINE`).
           Reset `exercise_rounds_count`, `level`, and `score` using tools.
         - No: Move to next sub topic using tool `next_sub_topic` and restart.

    4. **Completion**:

    - If all sub-topics are done, congratulate the user and summarize their performance (e.g., scores per sub-topic).
    Keep responses clear, encouraging, and beginner-friendly!
    don't add tool calls in the response. always think and refine the response
    """),
    add_state_in_messages=True,
    memory=memory,
    
    markdown=True,
    tools=[examine_mode, explain_mode, next_sub_topic, update_exercise_rounds_count,
           update_score, reset_exercise_count, reset_score, reset_level,update_understanding_level],
    add_datetime_to_instructions=True,
    

)

