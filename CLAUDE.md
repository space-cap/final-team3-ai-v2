# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Korean AI service project for automatic generation of KakaoTalk notification message templates. The project helps small business owners create compliant KakaoTalk notification templates by automatically generating policy-compliant templates from user input, solving the complex approval process barrier.

**Tech Stack:**
- AI: Python 3.13, OpenAI API, LangChain, Agents, Tools, RAG, LangGraph, Chroma, FastAPI
- Database: MySQL 8.4

## Development Environment

### Python Environment
- Python 3.13.5 is configured in `.venv/` virtual environment
- **IMPORTANT**: Always activate virtual environment before running any Python commands
- Activate virtual environment (Windows): `.venv\Scripts\activate`
- All pip installations and Python commands must be run within the activated virtual environment

### Project Structure

```
├── data/
│   └── policies/          # KakaoTalk notification policy documents (Korean)
│       ├── audit.md       # Audit guidelines
│       ├── black-list.md  # Blacklisted content
│       ├── content-guide.md # Content creation guidelines
│       ├── image.md       # Image usage policies
│       ├── infotalk.md    # Information message policies
│       ├── operations.md  # Operational guidelines
│       ├── publictemplate.md # Public template policies
│       └── white-list.md  # Whitelisted content
├── .venv/                 # Python virtual environment
└── README.md             # Project documentation (Korean)
```

## Key Data Sources

The `data/policies/` directory contains comprehensive KakaoTalk notification template policies in Korean that serve as the foundation for the AI template generation system. These policies include:

- **Content Guidelines**: Message formatting, character limits (1,000 chars), variable usage (`#{변수}`)
- **Operational Rules**: Spam prevention, legal compliance, message classification (informational vs. advertising)
- **Audit Requirements**: Template approval processes and violation consequences
- **Template Types**: Basic templates, supplementary information templates, and advertising elements

## Development Notes

- All policy documents are in Korean and contain specific KakaoTalk business messaging requirements
- The project is in early development phase with only basic structure established
- No application code, dependencies, or build scripts are currently present
- Virtual environment is set up but no packages are installed yet

## Common Development Tasks

Since this is an early-stage project, standard Python development workflows will apply:

- **Before any Python work**: Activate virtual environment with `.venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt` (when created)
- Install packages: `pip install <package_name>` (always in activated virtual environment)
- Run application: `python main.py` or similar (when created)
- Run tests: `pytest` or similar (when test framework is chosen)

The project will likely involve building RAG (Retrieval-Augmented Generation) systems using the policy documents in `data/policies/` to train/guide the AI template generation.