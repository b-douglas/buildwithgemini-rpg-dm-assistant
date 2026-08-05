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
import re
import secrets
from google.cloud import firestore

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


MODEL = "gemini-3.6-flash"
FIRESTORE_PROJECT = "qwiklabs-gcp-04-b94d5857ae5f"


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        # Memory service is absent during standalone local/eval runs
        pass
    return None


def get_story_beats(act: str = "") -> str:
    """Retrieves prepped campaign story beats from the Firestore database.

    Args:
        act: Optional filter by campaign act (e.g. 'Act I', 'Act II'). Leave empty to retrieve all beats.

    Returns:
        Formatted summary of story beats including title, act, summary, encounter type, and status.
    """
    try:
        db = firestore.Client(project=FIRESTORE_PROJECT)
        collection_ref = db.collection("story_beats")
        docs = list(collection_ref.stream())

        beats = []
        for doc in docs:
            data = doc.to_dict()
            if act and act.lower() not in data.get("act", "").lower():
                continue
            beats.append(data)

        if not beats:
            filter_msg = f" for act '{act}'" if act else ""
            return f"No story beats found in Firestore{filter_msg}."

        result = ["📖 **Campaign Story Beats (Firestore):**\n"]
        for b in beats:
            result.append(
                f"- **{b.get('title', 'Untitled')}** [{b.get('beat_id', '')}]\n"
                f"  - **Act:** {b.get('act', 'N/A')} | **Type:** {b.get('encounter_type', 'N/A')} | **Rec. Level:** {b.get('recommended_level', 5)} | **Status:** {b.get('status', 'prepped')}\n"
                f"  - **Summary:** {b.get('summary', '')}\n"
            )
        return "\n".join(result)
    except Exception as e:
        return f"Error reading story beats from Firestore: {str(e)}"


def save_story_beat(
    title: str,
    summary: str,
    act: str = "Act I",
    encounter_type: str = "Combat",
    recommended_level: int = 5,
    status: str = "prepped",
) -> str:
    """Saves a new campaign story beat or encounter prep into the Firestore database.

    Args:
        title: Title of the story beat or encounter.
        summary: Summary of the beat, narrative hook, and key monsters/NPCs.
        act: Campaign act name (e.g. 'Act I: Shadows over Oakhaven').
        encounter_type: Type of encounter ('Combat', 'Social', 'Exploration', 'Puzzle').
        recommended_level: Recommended average party level (1 to 20).
        status: Preparation status ('prepped', 'planned', 'completed').

    Returns:
        Confirmation message with the generated Firestore Beat ID.
    """
    try:
        db = firestore.Client(project=FIRESTORE_PROJECT)
        collection_ref = db.collection("story_beats")

        doc_count = len(list(collection_ref.stream()))
        beat_id = f"beat_{doc_count + 1:03d}"

        data = {
            "beat_id": beat_id,
            "title": title,
            "act": act,
            "summary": summary,
            "encounter_type": encounter_type,
            "recommended_level": recommended_level,
            "status": status,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        collection_ref.document(beat_id).set(data)
        return f"✅ Saved Story Beat '{title}' (ID: {beat_id}) to Firestore collection 'story_beats'."
    except Exception as e:
        return f"Error saving story beat to Firestore: {str(e)}"


def roll_dice(dice_expression: str) -> str:
    """Rolls D&D dice using cryptographically secure random numbers.

    Args:
        dice_expression: Expression like '1d20+5', '2d6+3', '1d100', '4d6'.

    Returns:
        String with detailed rolls, modifiers, and final total sum.
    """
    expr = dice_expression.lower().replace(" ", "")
    match = re.match(r"^(\d+)d(\d+)([\+\-]\d+)?$", expr)
    if not match:
        return f"Invalid dice format: '{dice_expression}'. Use format like '1d20+5' or '2d6'."

    num_dice = int(match.group(1))
    dice_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if num_dice < 1 or num_dice > 100:
        return "Error: Number of dice must be between 1 and 100."
    if dice_sides < 2 or dice_sides > 1000:
        return "Error: Dice sides must be between 2 and 1000."

    rolls = [secrets.randbelow(dice_sides) + 1 for _ in range(num_dice)]
    rolls_sum = sum(rolls)
    total = rolls_sum + modifier

    mod_str = f" {'+' if modifier >= 0 else ''}{modifier}" if modifier != 0 else ""
    return f"Rolled {dice_expression}: {rolls}{mod_str} = Total: {total}"


def rules_lawyer_lookup(topic: str) -> str:
    """Retrieves authoritative D&D 5e rules information.

    Args:
        topic: The rule, condition, or mechanic to look up (e.g., 'advantage', 'grappled', 'concentration', 'cover', 'resting').

    Returns:
        String summarizing the official 5e rules for the topic.
    """
    topic_clean = topic.lower().strip()
    rules_db = {
        "advantage": "Advantage: Roll two d20s and take the higher result. Disadvantage: Roll two d20s and take the lower result. Advantage and Disadvantage cancel each other out regardless of how many sources grant either.",
        "concentration": "Concentration: Taking damage requires a Constitution saving throw (DC 10 or half damage taken, whichever is higher). Casting another concentration spell or being incapacitated ends concentration.",
        "grappled": "Grappled: Speed becomes 0. Ends if grappler is incapacitated or an effect moves the target out of reach (e.g., Thunderwave, Shove).",
        "cover": "Half Cover: +2 AC and Dexterity saves. Three-Quarters Cover: +5 AC and Dexterity saves. Total Cover: Cannot be targeted directly by attacks or spells.",
        "resting": "Short Rest: 1 hour long. Spend Hit Dice to recover HP. Long Rest: 8 hours long. Regain all HP and up to half max Hit Dice. Max 1 Long Rest per 24 hours.",
        "death saves": "Death Saving Throws: At 0 HP, roll d20 on turn. 10+ is success, <10 is failure. 3 successes = stable; 3 failures = death. Natural 20 = regain 1 HP immediately. Natural 1 = 2 failures.",
    }
    for key, rule in rules_db.items():
        if key in topic_clean:
            return rule
    return f"Rule summary for '{topic}': Consult the Player's Handbook or Dungeon Master's Guide for specific rulings on {topic}."


def generate_random_encounter(party_level: int, difficulty: str = "Medium", environment: str = "Forest") -> str:
    """Generates a random D&D combat encounter tailored to party level, difficulty, and environment.

    Args:
        party_level: Average level of the player characters (1 to 20).
        difficulty: Desired difficulty ('Easy', 'Medium', 'Hard', 'Deadly').
        environment: Terrain type (e.g., 'Forest', 'Dungeon', 'Mountain', 'Swamp', 'Underdark').

    Returns:
        Formatted summary of the encounter including monsters, tactics, and environmental features.
    """
    return (
        f"⚔️ **Random Encounter [{difficulty.title()} - Level {party_level} in {environment.title()}]**\n"
        f"- **Monsters:** 2x Owlbears (CR 3) or 4x Bandits led by a Bandit Captain\n"
        f"- **Tactical Terrain:** {environment.title()} feature — Dense foliage / elevated cliffs providing half cover and difficult terrain.\n"
        f"- **Objective/Hook:** The creatures are guarding a hidden chest or ambushing travelers along the trail."
    )


def npc_impersonator(npc_role: str, tone: str = "mysterious", location: str = "Tavern") -> str:
    """Generates an NPC personality, dialogue snippet, and quest hook on the fly.

    Args:
        npc_role: The role or archetype of the NPC (e.g. 'Merchant', 'Guard', 'Blacksmith', 'Wizard', 'Innkeeper').
        tone: The tone/vibe of the interaction (e.g. 'mysterious', 'friendly', 'suspicious', 'panicked').
        location: Current setting (e.g. 'Tavern', 'Market Square', 'Castle Gate').

    Returns:
        String detailing NPC profile, sample dialogue, and secret motivation.
    """
    return (
        f"🎭 **NPC Profile: {npc_role.title()} ({tone.title()})**\n"
        f"- **Location:** {location}\n"
        f"- **Sample Dialogue:** \"Keep your voice down... around here, even the shadows have ears.\"\n"
        f"- **Secret Motivation:** Seeking help to recover a lost family heirloom from the local ruins."
    )


def adventure_flavor_text(location_type: str, atmosphere: str = "tense") -> str:
    """Generates sensory flavor text for the Dungeon Master to describe scenes to players.

    Args:
        location_type: Type of location (e.g. 'Ancient Tomb', 'Dark Forest', 'Flooded Cavern').
        atmosphere: Mood of the scene (e.g. 'tense', 'eerie', 'majestic', 'decaying').

    Returns:
        Sensory description suitable for reading aloud during game sessions.
    """
    return (
        f"📜 **Scene Description ({location_type} - {atmosphere.title()})**:\n"
        f"The air grows heavy with the scent of damp stone and ancient dust. Cold air clings to skin, "
        f"and echoing drips from unseen stalactites break the oppressive silence of the {location_type}."
    )


def get_image_asset_url(category: str = "locations", asset_name: str = "tomb_concept") -> str:
    """Generates the organized Cloud Storage public URL for an image asset.

    Args:
        category: Image category ('portraits', 'encounters', 'locations', 'items').
        asset_name: Name or description of the image asset (e.g. 'dragon_encounter', 'baron_vane_portrait').

    Returns:
        Public HTTPS URL for embedding the image asset in web pages or cards.
    """
    category_clean = category.lower().strip()
    valid_categories = {"portraits", "encounters", "locations", "items"}
    if category_clean not in valid_categories:
        category_clean = "locations"

    asset_slug = re.sub(r"[^a-z0-9_]", "_", asset_name.lower().strip())
    url = f"https://storage.googleapis.com/rpg-dm-images-qwiklabs-gcp-04-b94d5857ae5f/images/{category_clean}/{asset_slug}.png"
    return f"📷 **Asset URL ({category_clean.title()}):** {url}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the ultimate D&D 5e RPG Dungeon Master Assistant. "
        "You help Dungeon Masters manage campaign notes, roll dice, look up 5e rules, generate random encounters, "
        "impersonate NPCs with dialogue, describe immersive scenes, manage prepped campaign Story Beats in Firestore, "
        "and retrieve public Cloud Storage image asset URLs for character portraits, encounters, locations, and items. "
        "Always personalize responses based on remembered character facts, campaign beats, and player preferences."
    ),
    tools=[
        roll_dice,
        rules_lawyer_lookup,
        generate_random_encounter,
        npc_impersonator,
        adventure_flavor_text,
        get_story_beats,
        save_story_beat,
        get_image_asset_url,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
