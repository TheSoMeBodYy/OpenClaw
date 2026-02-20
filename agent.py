import ollama
import json
import re
from memory import LongTermMemory
from tools import (
    internet_search,
    add_todo,
    complete_todo,
    get_current_date,
)
from todo import load_todos

# Local LLM model used for reasoning
MODEL_NAME = "gemma:2b"


class Agent:
    """
    Core agent orchestration layer.

    Responsibilities:
    - Maintain short-term conversational context
    - Interface with long-term vector memory
    - Construct system prompt dynamically
    - Execute structured reasoning loop
    - Execute tools deterministically
    - Persist memory when instructed by the LLM
    """

    def __init__(self, config):
        self.config = config
        self.memory = LongTermMemory()

        # Short-term memory (conversation window)
        self.short_term = []

        # Internal debug log (visible in UI)
        self.internal_log = []

        # Maximum short-term memory size
        self.max_context = 6

    # ================= SYSTEM PROMPT =================

    def system_prompt(self, retrieved_memory):
        """
        Construct dynamic system prompt using:
        - User profile
        - Agent persona
        - Retrieved long-term memory
        - Tool usage constraints
        """
        return f"""
You are {self.config['agent_name']}.
Role: {self.config['agent_role']}.

System Instructions:
{self.config.get('system_instructions', '')}

User: {self.config['user_name']}
User Info: {self.config['user_info']}

Retrieved Memory:
{retrieved_memory}

Rules:
- Use tools ONLY if necessary.
- For normal knowledge questions, answer directly.
- Use add_todo only for explicit task creation.
- Use complete_todo only if user clearly says task is finished.
- Use date only for date requests.

Reasoning format:

{{
 "thought": "...",
 "action": "search | add_todo | complete_todo | date | none",
 "action_input": "...",
 "save_memory": true/false,
 "memory_content": "...",
 "final_answer": "..."
}}
"""

    # ================= SAFE JSON PARSER =================

    def safe_parse(self, text):
        """
        Defensive JSON parsing for smaller local models.
        Attempts full parse, then regex extraction fallback.
        """
        try:
            return json.loads(text)
        except:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    return None
            return None

    # ================= MODEL CALLS =================

    def call_model_json(self, messages):
        """
        Call LLM expecting structured JSON output.
        Used for reasoning loop.
        """
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                format="json",
                options={"temperature": 0.2}
            )
            return self.safe_parse(response["message"]["content"])
        except Exception as e:
            self.internal_log.append(f"Model JSON call failed: {str(e)}")
            return None

    def call_model_plain(self, messages):
        """
        Standard LLM call for natural language output.
        """
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            options={"temperature": 0.4}
        )
        return response["message"]["content"]

    # ================= PROACTIVITY =================

    def proactive_check(self):
        """
        Scan To-Do list and suggest action for unfinished tasks.
        Triggered on UI load.
        """
        todos = load_todos()
        for t in todos:
            if not t["done"]:
                msg = f"I see we still need to '{t['task']}'. Shall I handle it now?"
                self.internal_log.append("Proactive suggestion triggered.")
                return msg
        return None

    # ================= TOOL EXECUTION =================

    def execute_tool(self, action, action_input):
        """
        Deterministic tool execution layer.
        Logs tool selection and results.
        """
        self.internal_log.append(f"Tool selected: {action}")
        self.internal_log.append(f"Tool input: {action_input}")

        if action == "search":
            result = internet_search(action_input)
        elif action == "add_todo":
            result = add_todo(action_input)
        elif action == "complete_todo":
            result = complete_todo(action_input)
        elif action == "date":
            result = get_current_date()
        else:
            result = None

        if result:
            self.internal_log.append(f"Tool observation: {result}")

        return result

    # ================= MAIN REASONING PIPELINE =================

    def process_single_intent(self, user_input):
        """
        Hybrid reasoning strategy:
        - Deterministic routing for common intents
        - LLM JSON reasoning for complex cases
        """

        user_lower = user_input.lower().strip()

        # Always store user message first
        self.short_term.append({"role": "user", "content": user_input})
        self.short_term = self.short_term[-self.max_context:]

        # 1. Deterministic preference storage
        if (
            user_lower.startswith("i like")
            or user_lower.startswith("i love")
            or user_lower.startswith("i prefer")
            or user_lower.startswith("my favorite")
            or user_lower.startswith("remember")
        ) and not user_lower.endswith("?"):

            memory_fact = f"User preference: {user_input.strip()}"
            self.memory.add_memory(memory_fact)
            self.internal_log.append("Preference stored deterministically.")

            response = "Got it. I'll remember that."

            self.short_term.append({"role": "assistant", "content": response})
            self.short_term = self.short_term[-self.max_context:]

            return response

        # 2. Deterministic task completion
        if any(k in user_lower for k in ["i did", "i finished", "completed"]):
            response = complete_todo(user_input)

            self.short_term.append({"role": "assistant", "content": response})
            self.short_term = self.short_term[-self.max_context:]

            return response

        # 3. Deterministic task creation
        task_triggers = ["i need to", "i have to", "remind me to"]
        for trigger in task_triggers:
            if trigger in user_lower:
                task_text = user_lower.split(trigger)[-1].strip()
                response = add_todo(task_text)

                self.short_term.append({"role": "assistant", "content": response})
                self.short_term = self.short_term[-self.max_context:]

                return response

        # 4. Deterministic date handling
        if "today" in user_lower or "current date" in user_lower:
            response = get_current_date()

            self.short_term.append({"role": "assistant", "content": response})
            self.short_term = self.short_term[-self.max_context:]

            return response

        # 5. Knowledge guard (smart routing)
        knowledge_prefixes = ["what is", "who is", "define", "explain", "why"]

        if any(user_lower.startswith(p) for p in knowledge_prefixes):
            # Allow reasoning loop if question implies external lookup
            search_intent_keywords = ["search", "latest", "recent", "find", "trend", "news"]

            if not any(k in user_lower for k in search_intent_keywords):
                self.internal_log.append("Knowledge guard triggered.")
                response = self.call_model_plain([
                    {"role": "system", "content": f"You are {self.config['agent_role']}."},
                    {"role": "user", "content": user_input}
                ])

                self.short_term.append({"role": "assistant", "content": response})
                self.short_term = self.short_term[-self.max_context:]

                return response

        # 6. LLM reasoning loop

        retrieved = self.memory.query(user_input, k=2)
        retrieved_docs = retrieved.get("documents", [[]])[0]
        distances = retrieved.get("distances", [[]])[0] if "distances" in retrieved else []

        self.internal_log.append(f"Retrieved memory: {retrieved_docs}")
        self.internal_log.append(f"Distances: {distances}")

        messages = [
            {"role": "system", "content": self.system_prompt(retrieved_docs)}
        ] + self.short_term

        parsed = self.call_model_json(messages)

        if not parsed:
            response = self.call_model_plain(self.short_term)

            self.short_term.append({"role": "assistant", "content": response})
            self.short_term = self.short_term[-self.max_context:]

            return response

        thought = parsed.get("thought", "")
        action = parsed.get("action", "none")
        action_input = parsed.get("action_input", "")
        final_answer = parsed.get("final_answer", "") or ""
        save_memory = parsed.get("save_memory", False)
        memory_content = parsed.get("memory_content", "")

        self.internal_log.append(f"Thought: {thought}")

        if action != "none":
            observation = self.execute_tool(action, action_input)

            second_messages = [
                {"role": "system", "content": "Produce the final answer based on the observation."},
                {"role": "user", "content": f"Observation: {observation}"}
            ]

            final_answer = self.call_model_plain(second_messages)

        if not final_answer:
            self.internal_log.append("Final answer missing from JSON. Falling back to plain model.")
            final_answer = self.call_model_plain(self.short_term)

        self.internal_log.append(f"Thought: {thought}")

        if action != "none":
            observation = self.execute_tool(action, action_input)

            second_messages = [
                {"role": "system", "content": "Produce the final answer based on the observation."},
                {"role": "user", "content": f"Observation: {observation}"}
            ]

            final_answer = self.call_model_plain(second_messages)

        if save_memory and memory_content:
            self.memory.add_memory(memory_content)
            self.internal_log.append(f"Memory saved by LLM: {memory_content}")

        self.short_term.append({"role": "assistant", "content": final_answer})
        self.short_term = self.short_term[-self.max_context:]

        return final_answer

    def reasoning_loop(self, user_input):
        """
        Public reasoning entry point.
        """
        return self.process_single_intent(user_input)

    def get_working_memory(self):
        return self.short_term

    def get_internal_log(self):
        return self.internal_log
