# Contributing to GitHub Events Analytics

Thank you for considering contributing to GitHub Events Analytics! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
4. [Development Workflow](#development-workflow)
5. [Pull Request Process](#pull-request-process)
6. [Coding Standards](#coding-standards)
7. [Testing](#testing)
8. [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment following the instructions in the README.md
4. Create a new branch for your feature or bug fix

## How to Contribute

You can contribute to the project in several ways:

- **Reporting Bugs**: Create an issue describing the bug, including steps to reproduce, expected behavior, and actual behavior
- **Suggesting Enhancements**: Create an issue describing your enhancement suggestion with a clear title and detailed description
- **Code Contributions**: Submit a pull request with your changes
- **Documentation**: Improve or add documentation
- **Reviewing Pull Requests**: Review and comment on open pull requests

## Development Workflow

1. Create a new branch from `main` for your changes
2. Make your changes in small, logical commits
3. Add or update tests as necessary
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## Pull Request Process

1. Ensure your code follows the project's coding standards
2. Update the README.md or other documentation if necessary
3. Include tests for your changes
4. Ensure the test suite passes
5. Submit the pull request to the `main` branch
6. The pull request will be reviewed by maintainers
7. Address any feedback or requested changes
8. Once approved, your pull request will be merged

## Coding Standards

- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions small and focused on a single task
- Use type hints where appropriate
- Format code with Black and sort imports with isort

## Testing

- Write unit tests for all new functionality
- Ensure existing tests pass with your changes
- Run the test suite before submitting a pull request:
  ```
  ./run_tests.sh
  ```
- Aim for high test coverage

## Documentation

- Update documentation for any changed functionality
- Document new features or components
- Keep the README.md up to date
- Use clear and concise language
- Include examples where appropriate

Thank you for contributing to GitHub Events Analytics! 