## Taskmaster

Taskmaster is a process supervisor and manager. It allows you to manage and control a number of processes on UNIX-like operating systems.

## Requirements

- Python 3.11.7
- pipenv

## Installation

First, you need to install pipenv. Pipenv is a tool that aims to bring the best of all packaging worlds to the Python world. It harnesses Pipfile, pip, and virtualenv into one single command.

You can install pipenv using pip:

\`\`\`bash
pip install pipenv
\`\`\`

Install the project dependencies:

\`\`\`bash
pipenv install
\`\`\`

This will create a new virtual environment and install the dependencies. You can activate the virtual environment using:

\`\`\`bash
pipenv shell
\`\`\`

## Running the Project

To run the project, use the following command:

\`\`\`bash
python src/taskmaster.py config.yaml
\`\`\`

## Project Structure

- \`src/taskmaster.py\`: This is the main entry point of the application. It sets up and starts the Taskmaster application.
- \`src/process_manager.py\`: This file contains the \`ProcessManager\` class which is responsible for starting, stopping and managing processes.
- \`src/control_shell.py\`: This file contains the \`ControlShell\` class which is responsible for the interactive shell of the Taskmaster.
- \`src/config_parser.py\`: This file contains the \`ConfigParser\` class which is responsible for parsing the configuration file.
- \`src/logger.py\`: This file sets up the logger used throughout the application.
- \`config.yaml\`: This is the configuration file for the Taskmaster. It specifies the programs to be managed.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the terms of the MIT license."
