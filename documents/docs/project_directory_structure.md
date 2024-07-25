The UFO project is organized into a well-defined directory structure to facilitate development, deployment, and documentation. Below is an overview of each directory and file, along with their purpose:

```bash
📦project
 ┣ 📂documents               # Folder to store project documentation
 ┣ 📂learner                 # Folder to build the vector database for help documents
 ┣ 📂model_worker            # Folder to store tools for deploying your own model
 ┣ 📂record_processor        # Folder to parse human demonstrations from Windows Step Recorder and build the vector database
 ┣ 📂vetordb                 # Folder to store all data in the vector database for RAG (Retrieval-Augmented Generation)
 ┣ 📂logs                    # Folder to store logs, generated after the program starts
 ┗ 📂ufo                     # Directory containing main project code
    ┣ 📂module               # Directory for the basic module of UFO, e.g., session and round
    ┣ 📂agents               # Code implementation of agents in UFO
    ┣ 📂automator            # Implementation of the skill set of agents to automate applications
    ┣ 📂experience           # Parse and save the agent's self-experience
    ┣ 📂llm                  # Folder to store the LLM (Large Language Model) implementation
    ┣ 📂prompter             # Prompt constructor for the agent
    ┣ 📂prompts              # Prompt templates and files to construct the full prompt
    ┣ 📂rag                  # Implementation of RAG from different sources to enhance agents' abilities
    ┣ 📂utils                # Utility functions
    ┣ 📂config               # Configuration files
        ┣ 📜config.yaml      # User configuration file for LLM and other settings
        ┣ 📜config_dev.yaml  # Configuration file for developers
        ┗ ...
    ┗ 📄ufo.py               # Main entry point for the UFO client
```

## Directory and File Descriptions

### [documents]()
- **Purpose:** Stores all the project documentation.
- **Details:** This may include design documents, user manuals, API documentation, and any other relevant project documentation.

### [learner](https://github.com/microsoft/UFO/tree/main/learner)
- **Purpose:** Used to build the vector database for help documents.
- **Details:** This directory contains scripts and tools to process help documents and create a searchable vector database, enhancing the agents' ability for task completion.
### [model_worker](https://github.com/microsoft/UFO/tree/main/model_worker)
- **Purpose:** Contains tools and scripts necessary for deploying custom models.
- **Details:** This includes model deployment configurations, and management tools for integrating custom models into the project.
### [record_processor](https://github.com/microsoft/UFO/tree/main/record_processor)
- **Purpose:** Parses human demonstrations recorded using the Windows Step Recorder and builds the vector database.
- **Details:** This directory includes parsers, data processing scripts, and tools to convert human demonstrations into a format suitable for agent's retrieval.
### [vetordb](https://github.com/microsoft/UFO/tree/main/vectordb)
- **Purpose:** Stores all data within the vector database for Retrieval-Augmented Generation (RAG).
- **Details:** This directory is essential for maintaining the data that enhances the agents' ability to retrieve relevant information and generate more accurate responses.
### [logs]()
- **Purpose:** Stores log files generated by the application.
- **Details:** This directory helps in monitoring, debugging, and analyzing the application's performance and behavior. Logs are generated dynamically as the application runs.
### [ufo](https://github.com/microsoft/UFO/tree/main/ufo)
- **Purpose:** The core directory containing the main project code.
- **Details:** This directory is further subdivided into multiple subdirectories, each serving a specific purpose within the project.

    #### [module](https://github.com/microsoft/UFO/tree/main/ufo/module)
    - **Purpose:** Contains the basic modules of the UFO project, such as session management and rounds.
    - **Details:** This includes foundational classes and functions that are used throughout the project.
    #### [agents](https://github.com/microsoft/UFO/tree/main/ufo/agents)
    - **Purpose:** Houses the code implementations of various agents in the UFO project.
    - **Details:** Agents are components that perform specific tasks within the system, and this directory contains their logic, components, and behavior.
    #### [automator](https://github.com/microsoft/UFO/tree/main/ufo/automator)
    - **Purpose:** Implements the skill set of agents to automate applications.
    - **Details:** This includes scripts and tools that enable agents to interact with and automate tasks in various applications, such as mouse and keyboard actions and API calls.
    #### [experience](https://github.com/microsoft/UFO/tree/main/ufo/experience)
    - **Purpose:** Parses and saves the agent's self-experience.
    - **Details:** This directory contains mechanisms for agents to learn from their actions and outcomes, improving their performance over time.
    #### [llm](https://github.com/microsoft/UFO/tree/main/ufo/llm)
    - **Purpose:** Stores the implementation of the Large Language Model (LLM).
    - **Details:** This includes the implementation of APIs for different language models, such as GPT, Genimi, QWEN, etc., that are used by the agents.
    #### [prompter](https://github.com/microsoft/UFO/tree/main/ufo/prompter)
    - **Purpose:** Constructs prompts for the agents.
    - **Details:** This directory includes prompt construction logic and tools that help agents generate meaningful prompts for user interactions.
    #### [prompts](https://github.com/microsoft/UFO/tree/main/ufo/prompts)
    - **Purpose:** Contains prompt templates and files used to construct the full prompt.
    - **Details:** This includes predefined prompt structures and content that are used to create meaningful interactions with the agents.
    #### [rag](https://github.com/microsoft/UFO/tree/main/ufo/rag)
    - **Purpose:** Implements Retrieval-Augmented Generation (RAG) from different sources to enhance the agents' abilities.
    - **etails:** This directory includes scripts and tools for integrating various data sources into the RAG framework, improving the accuracy and relevance of the agents' outputs.
    #### [utils](https://github.com/microsoft/UFO/tree/main/ufo/utils)
    - **Purpose:** Contains utility functions.
    - **Details:** This directory includes helper functions, common utilities, and other reusable code snippets that support the project's operations.
    #### [config](https://github.com/microsoft/UFO/tree/main/ufo/config)
    - **Purpose:** Stores configuration files.
    - **Details:** This directory includes different configuration files for various environments and purposes.
    - **[config.yaml:](https://github.com/microsoft/UFO/blob/main/ufo/config/config.yaml.template)** User configuration file for LLM and other settings. You need to rename `config.yaml.template` to `config.yaml` and edit the configuration settings as needed.
    - **[config_dev.yaml](https://github.com/microsoft/UFO/blob/main/ufo/config/config_dev.yaml):** Developer-specific configuration file with settings tailored for development purposes.
    #### [ufo.py](https://github.com/microsoft/UFO/blob/main/ufo/ufo.py)
    - **Purpose:** Main entry point for the UFO client.
    - **Details:** This script initializes and starts the UFO application.








