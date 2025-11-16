# Contributing to Enterprise SIEM

Thank you for your interest in contributing to the Enterprise SIEM project! This document provides guidelines for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Process](#development-process)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Security Issues](#security-issues)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. We expect all participants to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

1. Read the [QUICKSTART.md](QUICKSTART.md) guide
2. Set up your development environment
3. Familiarize yourself with the architecture (see [docs/architecture/DESIGN.md](docs/architecture/DESIGN.md))

### Setting Up Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/enterprise-siem.git
cd enterprise-siem

# Add upstream remote
git remote add upstream https://github.com/your-org/enterprise-siem.git

# Install development dependencies
make dev-setup

# Start development environment
docker-compose up -d
```

## Development Process

### 1. Choose an Issue

- Check the [issue tracker](https://github.com/your-org/enterprise-siem/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to let others know you're working on it

### 2. Create a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/issue-number-description
# or
git checkout -b fix/issue-number-description
```

**Branch Naming Convention:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### 3. Make Changes

- Write clean, readable code
- Follow coding standards (see below)
- Add tests for new features
- Update documentation as needed

### 4. Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat(collector): add support for Windows Event Logs"
git commit -m "fix(api): resolve authentication timeout issue"
git commit -m "docs(architecture): update data model diagram"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### 5. Push and Create Pull Request

```bash
git push origin feature/issue-number-description
```

Then create a pull request on GitHub.

## Coding Standards

### Go Code Standards

Follow [Effective Go](https://golang.org/doc/effective_go) and [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments).

```go
// Good: Clear, concise function with documentation
// ProcessEvent normalizes and enriches a raw event
func ProcessEvent(ctx context.Context, rawEvent []byte) (*Event, error) {
    if len(rawEvent) == 0 {
        return nil, fmt.Errorf("empty event")
    }

    event, err := parseEvent(rawEvent)
    if err != nil {
        return nil, fmt.Errorf("parse event: %w", err)
    }

    return event, nil
}
```

**Go Best Practices:**
- Use `gofmt` and `golint`
- Handle errors explicitly
- Use context for cancellation
- Write table-driven tests
- Keep functions small and focused
- Use meaningful variable names
- Add package and function comments

### Python Code Standards

Follow [PEP 8](https://pep8.org/) and use type hints.

```python
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def detect_anomaly(
    events: List[dict],
    threshold: float = 0.95
) -> Optional[dict]:
    """
    Detect anomalies in event stream using ML model.

    Args:
        events: List of event dictionaries
        threshold: Anomaly score threshold (0.0-1.0)

    Returns:
        Anomaly details if detected, None otherwise
    """
    if not events:
        logger.warning("Empty event list provided")
        return None

    # Implementation here
    pass
```

**Python Best Practices:**
- Use `black` for formatting
- Use `pylint` and `mypy`
- Write docstrings for all functions
- Use type hints
- Follow PEP 8 naming conventions
- Use virtual environments

### TypeScript/React Code Standards

Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).

```typescript
interface Event {
  id: string;
  timestamp: Date;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
}

// Good: Typed component with clear prop interface
interface EventListProps {
  events: Event[];
  onEventClick?: (event: Event) => void;
}

export const EventList: React.FC<EventListProps> = ({ events, onEventClick }) => {
  return (
    <div className="event-list">
      {events.map(event => (
        <EventCard
          key={event.id}
          event={event}
          onClick={() => onEventClick?.(event)}
        />
      ))}
    </div>
  );
};
```

**TypeScript/React Best Practices:**
- Use TypeScript for all new code
- Use functional components with hooks
- Use Prettier for formatting
- Use ESLint
- Write prop types/interfaces
- Use meaningful component names

### General Standards

- **Comments**: Write clear, concise comments explaining "why", not "what"
- **Naming**: Use descriptive names for variables, functions, and classes
- **DRY**: Don't Repeat Yourself - extract common logic
- **KISS**: Keep It Simple, Stupid - avoid unnecessary complexity
- **Error Handling**: Handle errors gracefully with meaningful messages
- **Logging**: Use structured logging with appropriate levels

## Testing Guidelines

### Unit Tests

All new code must include unit tests.

**Go:**
```go
func TestProcessEvent(t *testing.T) {
    tests := []struct {
        name    string
        input   []byte
        want    *Event
        wantErr bool
    }{
        {
            name:  "valid event",
            input: []byte(`{"type":"login","user":"admin"}`),
            want:  &Event{Type: "login", User: "admin"},
            wantErr: false,
        },
        {
            name:    "empty event",
            input:   []byte{},
            want:    nil,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ProcessEvent(context.Background(), tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ProcessEvent() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("ProcessEvent() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

**Python:**
```python
import pytest
from siem.analyzer import detect_anomaly

def test_detect_anomaly_empty_events():
    result = detect_anomaly([])
    assert result is None

def test_detect_anomaly_normal_behavior():
    events = [{"score": 0.5}, {"score": 0.6}]
    result = detect_anomaly(events, threshold=0.95)
    assert result is None

def test_detect_anomaly_detected():
    events = [{"score": 0.99}]
    result = detect_anomaly(events, threshold=0.95)
    assert result is not None
    assert result["score"] == 0.99
```

**TypeScript/React:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { EventList } from './EventList';

describe('EventList', () => {
  const mockEvents = [
    { id: '1', timestamp: new Date(), severity: 'high', message: 'Test' }
  ];

  it('renders events', () => {
    render(<EventList events={mockEvents} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('calls onEventClick when event is clicked', () => {
    const handleClick = jest.fn();
    render(<EventList events={mockEvents} onEventClick={handleClick} />);

    fireEvent.click(screen.getByText('Test'));
    expect(handleClick).toHaveBeenCalledWith(mockEvents[0]);
  });
});
```

### Integration Tests

Test interactions between components.

```go
func TestEventPipeline(t *testing.T) {
    // Setup test Kafka, Elasticsearch
    // Send event through pipeline
    // Verify event is indexed correctly
}
```

### Running Tests

```bash
# Go tests
make test-go

# Python tests
make test-python

# Frontend tests
make test-frontend

# All tests
make test

# With coverage
make test-coverage
```

### Test Coverage

Minimum coverage requirements:
- New code: 80%
- Critical paths: 90%
- Overall project: 75%

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code follows style guidelines
3. ✅ Documentation updated
4. ✅ Commit messages follow conventions
5. ✅ No merge conflicts

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally

## Related Issues
Closes #123
```

### Review Process

1. Automated checks run (linting, tests, security scans)
2. At least 2 reviewers approve
3. All comments addressed
4. Squash and merge to main

### After Merge

- Delete your branch
- Update your local main branch
- Close related issues

## Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email security@example.com
2. Include detailed description
3. Provide steps to reproduce
4. Wait for confirmation before disclosure

We will:
- Acknowledge within 48 hours
- Provide timeline for fix
- Credit you in release notes (unless you prefer anonymity)

## Development Guidelines

### Performance Considerations

- Profile before optimizing
- Use benchmarks for performance-critical code
- Consider memory allocation in hot paths
- Use connection pooling
- Implement caching where appropriate

### Security Considerations

- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Follow principle of least privilege
- Never commit secrets
- Use secure defaults

### Documentation

Update documentation for:
- New features
- API changes
- Configuration options
- Deployment procedures

## Communication

- **GitHub Issues**: Bug reports, feature requests
- **Pull Requests**: Code review, discussion
- **Slack**: #siem-dev channel for quick questions
- **Monthly Meetings**: Architecture discussions

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to contributor meetings

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

- Read the documentation in `/docs`
- Check existing issues
- Ask in #siem-dev Slack channel
- Email dev@example.com

Thank you for contributing! 🎉
