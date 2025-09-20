# Gemini Subagent Usage Examples

## Overview
This document provides practical examples of using the Gemini subagent for various development tasks.

## Prerequisites
1. Ensure `.env` file contains valid `GEMINI_API_KEY`
2. Gemini CLI is installed and accessible
3. Gemini subagent is registered in `.claude/agents/`

## Basic Usage Pattern
```bash
source .env && echo "your prompt here" | gemini -m gemini-2.5-pro
```

## Example 1: Code Review

### Python Code Review
```bash
source .env && echo "Please review this Python function for best practices, security, and optimization:

def process_user_input(user_data):
    result = eval(user_data)
    return result" | gemini -m gemini-2.5-pro
```

### JavaScript Code Review
```bash
source .env && echo "Analyze this JavaScript code for potential issues:

function fetchData() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'https://api.example.com/data', false);
    xhr.send();
    return JSON.parse(xhr.responseText);
}" | gemini -m gemini-2.5-pro
```

## Example 2: Bug Detection and Analysis

### Debugging Help
```bash
source .env && echo "I'm getting a 'TypeError: Cannot read property of undefined' error in this code. Can you help identify the issue?

const users = [
    { name: 'John', age: 30 },
    { name: 'Jane' }
];

users.forEach(user => {
    console.log(user.name + ' is ' + user.age + ' years old');
});" | gemini -m gemini-2.5-pro
```

## Example 3: Performance Optimization

### Algorithm Optimization
```bash
source .env && echo "Can you optimize this sorting algorithm for better performance?

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr" | gemini -m gemini-2.5-pro
```

## Example 4: Documentation Generation

### API Documentation
```bash
source .env && echo "Generate API documentation for this Python function:

def create_user(username, email, password, role='user'):
    '''Create a new user account'''
    if not username or not email or not password:
        raise ValueError('Missing required fields')

    hashed_password = hash_password(password)
    user = User(username=username, email=email, password=hashed_password, role=role)
    user.save()
    return user" | gemini -m gemini-2.5-pro
```

## Example 5: Code Translation

### Python to JavaScript
```bash
source .env && echo "Convert this Python code to equivalent JavaScript:

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

numbers = [fibonacci(i) for i in range(10)]
print(numbers)" | gemini -m gemini-2.5-pro
```

## Example 6: Testing Strategy

### Unit Test Generation
```bash
source .env && echo "Generate comprehensive unit tests for this function:

def calculate_discount(price, discount_percent, is_premium_member=False):
    if price < 0 or discount_percent < 0 or discount_percent > 100:
        raise ValueError('Invalid input values')

    discount = price * (discount_percent / 100)
    if is_premium_member:
        discount *= 1.1  # 10% additional discount for premium members

    return max(0, price - discount)" | gemini -m gemini-2.5-pro
```

## Example 7: Architecture Analysis

### System Design Review
```bash
source .env && echo "Review this microservices architecture and suggest improvements:

Services:
- User Service (handles authentication, user profiles)
- Product Service (manages product catalog)
- Order Service (processes orders)
- Payment Service (handles payments)
- Notification Service (sends emails/SMS)

Current issues:
- Direct service-to-service calls
- No centralized logging
- Manual deployment process" | gemini -m gemini-2.5-pro
```

## Example 8: Database Query Optimization

### SQL Optimization
```bash
source .env && echo "Optimize this SQL query for better performance:

SELECT u.username, p.title, c.comment_text, c.created_at
FROM users u
JOIN posts p ON u.id = p.user_id
JOIN comments c ON p.id = c.post_id
WHERE u.created_at > '2024-01-01'
ORDER BY c.created_at DESC;" | gemini -m gemini-2.5-pro
```

## Rate Limiting Considerations
- Free tier: 5 requests/minute, 25 requests/day
- For complex analysis, break into smaller parts
- Use `gemini-2.5-flash` for simpler tasks to save quota

## Best Practices
1. **Clear Context**: Provide specific context and requirements
2. **Code Quality**: Ask for best practices, security, and performance
3. **Error Handling**: Include error scenarios in your prompts
4. **Documentation**: Request explanations for complex solutions
5. **Multiple Options**: Ask for alternative approaches when applicable

## Troubleshooting
- If API key errors occur, verify `.env` file and reload with `source .env`
- For rate limit errors, wait before retrying
- Use shorter prompts to stay within token limits