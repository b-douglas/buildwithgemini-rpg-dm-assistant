# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


MODEL = "gemini-3.6-flash"


async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


def calculate(expression: str) -> str:
    """Evaluates a mathematical expression.

    Args:
        expression: A string containing a mathematical expression, e.g. '12 * 45 + 7' or '2 ** 8'.

    Returns:
        A string with the result of the calculation.
    """
    try:
        clean_expr = expression.replace("^", "**")
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
            "sum": sum,
        }
        result = eval(clean_expr, {"__builtins__": None}, allowed_names)
        return f"The result of {expression} is {result}."
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"


def calculate_percentage(part: float, total: float) -> str:
    """Calculates what percentage 'part' is of 'total'.

    Args:
        part: The partial number.
        total: The total number.

    Returns:
        A string with the percentage result.
    """
    if total == 0:
        return "Error: total cannot be 0."
    pct = (part / total) * 100
    return f"{part} is {pct:.2f}% of {total}."


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a helpful RPG Dungeon Master Assistant. You remember campaign notes, player preferences, and character facts from previous sessions and use them to personalize your responses.",
    tools=[calculate, calculate_percentage, PreloadMemoryTool()],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
