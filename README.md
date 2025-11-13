# Movi - The Multimodal Transport Agent  multimodal

[cite_start]Welcome to "Movi," a prototype for a next-generation, knowledge-aware AI assistant for the MoveInSync transport platform[cite: 3, 13]. [cite_start]This project demonstrates a robust, stateful, and multimodal AI agent built using `langgraph` to help transport managers with their complex daily tasks[cite: 14, 19].

[cite_start]Movi understands the platform's core logic ($Stop \rightarrow Path \rightarrow Route \rightarrow Trip$) and, most critically, understands the consequences of actions, such as removing a vehicle from a booked trip[cite: 16].

## ✨ Core Features

* **🎙️ Multimodal I/O:** Interact with Movi using both **text** and **voice (Speech-to-Text)**. [cite_start]Movi responds in text and with **spoken audio (Text-to-Speech)**[cite: 159, 160].
* **🧠 "Tribal Knowledge" Consequence Flow:** Movi's core `langgraph` logic prevents costly errors. [cite_start]If a user tries to perform a risky action (e.g., "Remove vehicle from 'Bulk - 00:01'"), the agent first checks for consequences (like existing bookings) and asks for user confirmation before proceeding[cite: 176, 186].
* **📸 Image-Based Actions:** Movi can process multimodal inputs. [cite_start]A user can upload a screenshot of the dashboard, point to a trip, and say, "Remove the vehicle from *this* trip"[cite: 191]. The agent uses a vision model to identify the entity and triggers the same consequence flow.
* [cite_start]**📄 UI Context-Awareness:** The Movi agent is aware of which page the user is on (e.g., `busDashboard` or `manageRoute`) and provides relevant help and actions for that specific context[cite: 153].
* **🛠️ 10+ Database Tools:** Movi is connected to the transport database and can perform over 10 distinct actions, including:
    * [cite_start]**Read (Dynamic):** "What's the status of the 'Bulk - 00:01' trip?" [cite: 167]
    * [cite_start]**Read (Static):** "List all stops for 'Path-2'." [cite: 168]
    * [cite_start]**Create (Dynamic):** "Assign vehicle 'MH-12-3456' to the 'Path Path - 00:02' trip." [cite: 170]
    * [cite_start]**Delete (Dynamic):** "Remove the vehicle from 'Bulk - 00:01'." [cite: 172]
    * [cite_start]**Create (Static):** "Create a new stop called 'Odeon Circle'." [cite: 173]
    * ...and many more.

## ⚙️ Tech Stack

* **Frontend:** React, Vite, Tailwind CSS
* **Backend:** Python 3.11+, FastAPI
* **Database:** SQLite (for prototype simplicity)
* **AI Agent:** `langgraph`
* **LLMs & APIs:**
    * **Reasoning & Vision:** OpenAI GPT-4o
    * **Speech-to-Text:** OpenAI Whisper
    * **Text-to-Speech:** OpenAI TTS-1

## 📐 Architecture & `langgraph` Design

This project is a full-stack application. The **React frontend** communicates with a **FastAPI backend**. The backend serves the Movi AI agent, which uses `SQLAlchemy` (or similar) to interact with the **SQLite** database.

The core of the backend is the `langgraph` agent, designed to be stateful and manage conditional logic.

### 1. Agent State (`AgentState`)

The graph's state is defined to hold all necessary information as it moves between nodes:

```python
class AgentState(TypedDict):
    # Conversation history
    messages: Annotated[list, add_messages]
    
    # Current page user is on
    currentPage: str
    
    # Entities extracted from user query or vision
    trip_name: str
    vehicle_plate: str
    driver_name: str
    path_name: str
    
    # State for the "Consequence Flow"
    confirmation_pending: bool  # Is the graph waiting for a "yes/no"?
    consequence_info: str       # Stores the warning message (e.g., "25% booked")
    action_to_confirm: str      # Stores the risky function to run (e.g., "remove_vehicle")
