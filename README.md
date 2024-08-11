# Taskmaster

Taskmaster is a process supervisor and manager designed for UNIX-like operating systems. It allows you to manage and control multiple processes efficiently.

## Requirements

- Python 3.11.7
- pipenv

## Installation

1. Install pipenv:
   ```bash
   pip install pipenv
   ```

2. Install project dependencies:
   ```bash
   pipenv install
   ```

3. Activate the virtual environment:
   ```bash
   pipenv shell
   ```

## Running the Project

To run Taskmaster, use the following command:

```bash
python src/taskmaster.py config.yaml
```

## Project Structure

- `src/taskmaster.py`: Main entry point of the application.
- `src/process_manager.py`: Contains the `ProcessManager` class for process management.
- `src/control_shell.py`: Implements the `ControlShell` class for the interactive shell.
- `src/config_parser.py`: Houses the `ConfigParser` class for configuration file parsing.
- `src/logger.py`: Sets up the application-wide logger.
- `config.yaml`: Configuration file specifying the programs to be managed.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
