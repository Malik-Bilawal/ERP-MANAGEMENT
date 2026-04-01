# AGENTS.md - Agentic Coding Guidelines

This document provides guidelines for AI agents working in this codebase.

## Project Overview

ISM (Information Service Management) is a Django REST backend with a Next.js frontend for managing clients, projects, services, and finances.

- **Backend**: Django 6.0 + Django REST Framework + MySQL
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind CSS v4

## Build/Lint/Test Commands

### Frontend (`frontend/srf-front/`)

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Run ESLint on all files
npm run lint

# Run ESLint on specific file
npm run lint -- src/app/page.tsx
```

### Backend (`backend/`)

```bash
# Run Django development server
python manage.py runserver

# Run Django with custom port
python manage.py runserver 8080

# Apply migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test client_management

# Run specific test class
python manage.py test client_management.tests.ClientModelTest

# Run specific test method
python manage.py test client_management.tests.ClientModelTest.test_client_creation

# Check for issues
python manage.py check

# Shell
python manage.py shell
```

## Code Style Guidelines

### Python (Django)

**Imports Order**
1. Standard library (`os`, `logging`, `typing`)
2. Third-party (`django`, `rest_framework`, etc.)
3. Local app (`from .models import`, `from .serializers import`)

**Naming Conventions**
- Models: `PascalCase` (e.g., `Client`, `Project`)
- Model fields: `snake_case` (e.g., `client_id`, `created_at`)
- ViewSets: `PascalCase` ending with `ViewSet` (e.g., `ClientViewSet`)
- Serializers: `PascalCase` ending with `Serializer` (e.g., `ClientSerializer`)
- URLs: lowercase with underscores (e.g., `client-management/`)
- Constants: `UPPER_SNAKE_CASE`

**Model Conventions**
```python
class Client(models.Model):
    """Model description."""

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        indexes = [
            models.Index(fields=['client_id']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.client_id} - {self.name}"
```

**ViewSet Conventions**
- Use `ModelViewSet` for CRUD operations
- Always set `permission_classes = [permissions.IsAuthenticated]`
- Use `filter_backends` for search and ordering
- Define `search_fields` and `ordering_fields`
- Use `@action` decorators for custom endpoints
- Use `get_queryset()` for custom filtering

**Serializer Conventions**
- Use `ModelSerializer` for model serialization
- Define `read_only_fields` for auto-populated fields
- Use `source` for nested field access
- Include related object names as read-only fields (e.g., `client_name`)

**Error Handling**
- Use DRF's `Response` with appropriate HTTP status codes
- Return validation errors via `serializer.errors`
- Use `raise_validation_error()` for custom validation
- Log errors appropriately using Python's `logging` module

### TypeScript/JavaScript (Next.js)

**Naming Conventions**
- Components: `PascalCase` (e.g., `ClientList.tsx`)
- Hooks: `camelCase` starting with `use` (e.g., `useClientData`)
- Utils: `camelCase` (e.g., `formatDate.ts`)
- Types/Interfaces: `PascalCase` (e.g., `ClientType.ts`)
- Constants: `UPPER_SNAKE_CASE`

**File Structure**
```
src/app/          # Next.js App Router pages
src/components/   # React components
src/lib/          # Utilities and helpers
src/types/        # TypeScript types
```

**React/TypeScript Patterns**
- Use functional components with arrow functions or `function` keyword
- Define interfaces for component props
- Use `use client` directive for client-side components
- Prefer composition over prop drilling
- Use early returns for conditional rendering

**Tailwind CSS**
- Use utility classes from Tailwind CSS v4
- Follow existing color scheme in `globals.css`
- Use `dark:` prefix for dark mode variants
- Use `cn()` utility for conditional classes

**ESLint Configuration**
- Uses `eslint-config-next` (Next.js recommended rules)
- Extends both `core-web-vitals` and `typescript` configs

### General Guidelines

**Database**
- Always use migrations for schema changes
- Use `related_name` for reverse relationships
- Add indexes for frequently queried fields
- Use `DecimalField` for monetary values (never FloatField)

**API Design**
- RESTful endpoints via ViewSets
- Use pagination (`PageNumberPagination`, default page size 10)
- Filter backends for search and ordering

**Admin Interface**
- Uses Unfold theme for Django admin
- Configure sidebar navigation in `settings.py` under `UNFOLD['SIDEBAR']`

## Database Configuration

- **Engine**: MySQL
- **Port**: 3308
- **Database**: `srf_ims_db`
- **Settings**: Located in `backend/backend/settings.py`

## Key Dependencies

### Backend
- Django==6.0.3
- djangorestframework==3.16.1
- django-cors-headers==4.9.0
- mysqlclient==2.2.8
- python-dotenv==1.2.2
- django-filter==24.3
- Pillow==11.1.0

### Frontend
- next==16.1.6
- react==19.2.3
- tailwindcss==4
- typescript==5
- eslint==9
- eslint-config-next==16.1.6

## Important Notes

1. **No test framework configured**: Test files exist but are empty. Consider adding pytest for Python and Jest for JavaScript.

2. **React Compiler**: Frontend uses experimental React Compiler (`babel-plugin-react-compiler`).

3. **Authentication**: Uses session-based auth with BasicAuth fallback.

4. **Secrets**: Uses `.env` file with `python-dotenv`. Never commit secrets.

5. **Media/Static Files**: Configure in `settings.py` (MEDIA_ROOT, STATIC_ROOT).