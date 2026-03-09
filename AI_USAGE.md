# AI Usage Disclosure

## AI Assistant Built Into the App
This application includes an **optional** AI Assistant feature powered by **Google Gemini 2.5 Flash**.

We integrated this through the official `google-genai` Python SDK. The architecture is as follows:
1. **API Setup**: The Gemini API key is loaded from `.streamlit/secrets.toml`. If the key is missing or invalid, the app gracefully falls back to normal operation without crashing. 
2. **Context Sending**: To preserve memory and stay within token limits, we pass a highly compressed "Data Profile" to Gemini instead of the whole dataset. This includes column names, types, null percentages, and just ~3-5 sample rows for context.
3. **Structured Extraction**: For cleaning operations and chart suggestions, we heavily utilized the **Structured Output (JSON schema) capabilities** using `pydantic`. This forces the LLM to reply precisely in a format our application can parse, bridging the gap between natural language unpredictability and strict Python UI rendering.

### AI Features Included (+12 Bonus Points)
* **Data Dictionary Generator**: Available on the Upload page. Automatically infers column meanings and checks for potential anomalies, outputting a clear markdown table.
* **Natural Language Cleaning**: Available in the Cleaning Studio. Users type instructions like "Fill missing ages with median", and the system maps this to actionable stream processing cards using our `utils/cleaning.py` pipeline rules.
* **Smart Chart Suggestions**: Available in the Visualization builder. It analyzes data types and outputs JSON matching our pre-defined charts (e.g., automatically recommending a Box Plot comparing numeric salaries against categorical departments).
* **AI Chat & Code Snippets**: A dedicated sidebar chat interface streams context-aware answers, helping users write Pandas code snippets mirroring the dashboard UI operations.

## AI Tools Used During Development Workflow
During the coding of this project, we primarily used two tools:
* **Google Gemini (antigravity agent)**
* **Anthropic Claude 3.5 Sonnet / ChatGPT**

### How AI Was Used:
1. **Brainstorming Architecture**: We used AI to help brainstorm the modular file structure (putting pages in `pages/`, tools in `utils/`).
2. **Refactoring Code**: Early in the project, the `cleaning_studio.py` file got too large. We used Claude to help extract standard functions (like dealing with outliers, scaling numeric values, and grouping strings) into `utils/cleaning.py`.
3. **Regex Patterns**: We utilized LLMs to generate the regular expression rules applied when detecting dirty data (like currency symbols and percentage signs).
4. **Testing Syntax**: We prompted an AI to generate the skeleton mock inputs for `pytest` testing our more complex functions (like our Transform Log undoing mechanics).
5. **Streamlit Chat Integration**: We used an AI coding assistant to help understand how Streamlit's `st.write_stream()` and `st.status()` interact with generator objects, which greatly saved us time reading external documentation.

### Proof of Concept vs AI
All original logic for the *data transformations* remains pure Python and Pandas. The AI generates the configurations (the parameters to feed our pipeline), it does not directly modify the backing memory of the DataFrame. We made sure to maintain strict boundaries.
