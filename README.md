# ProjectForge

**ProjectForge** is a student team collaboration platform built with Django. It helps student teams organize projects, milestones, tasks, members, discussions, and project activity in one workspace.

## Features

- **Authentication:** User registration, login, and logout.
- **Project Management:** Create, view, edit, and delete projects with public or private visibility.
- **Member Management:** Add and remove project members with Lead and Member roles.
- **Milestones:** Create, edit, and delete milestones with due dates.
- **Task Management:** Create, assign, edit, and delete tasks with status and priority.
- **Comments:** Discuss tasks through comments.
- **Activity Feed:** Review important project events.
- **In-App Notifications:** Receive notifications about assignments, comments, membership changes, completed tasks, and milestone due dates.
- **Kanban Board:** Planned feature.

## Technology Stack

- **Backend:** Python, Django
- **Database:** SQLite for local development
- **Frontend:** Django Templates, HTML, CSS, TypeScript
- **Frontend Tooling:** Bun
- **Python Dependency Management:** uv

## Prerequisites

Install the following tools before running the project:

- Python version specified in `.python-version`
- uv
- Bun

## Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd ProjectForge
```

Replace `<YOUR_REPOSITORY_URL>` with the repository URL after publishing the project.

### 2. Install Python dependencies

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=replace-with-your-own-secret-key
```

Keep `.env` private. Never commit it to Git.

### 4. Apply database migrations

```bash
uv run python manage.py migrate
```

### 5. Build frontend assets

```bash
bun install
bun run build
```

### 6. Start the development server

```bash
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Running Tests

Run the Django test suite:

```bash
uv run python manage.py test
```

Check the Django configuration:

```bash
uv run python manage.py check
```

Check TypeScript:

```bash
bunx tsc
```

## Project Structure

```text
ProjectForge/
├── accounts/       # Authentication and account pages
├── config/         # Django project configuration
├── static/
│   ├── css/        # Stylesheets
│   ├── src/ts/     # TypeScript source
│   └── dist/       # Generated frontend assets (Git-ignored)
├── templates/      # Shared Django templates
├── workspaces/     # Projects, milestones, tasks, and collaboration
├── manage.py
├── package.json
├── pyproject.toml
├── uv.lock
├── bun.lock
└── README.md
```

## Security Notes

- Store `DJANGO_SECRET_KEY` in `.env`.
- Do not commit `.env`, the local SQLite database, virtual environments, or generated dependencies.
- `DEBUG = True` is intended for local development, not public production deployment.

## Project Status

ProjectForge is being developed as a college project. Features and documentation may evolve as development continues.
