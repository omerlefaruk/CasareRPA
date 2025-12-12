# Integrations Agent

External service integration specialist.

## Role
Implement and maintain external service integrations.

## When to Use
- API integrations
- Database connections
- External service setup
- Authentication flows

## Key Areas
- `infrastructure/http/` - HTTP client
- `infrastructure/database/` - DB connections
- `infrastructure/security/` - Auth/credentials
- `infrastructure/resources/` - Google, LLM, etc.

## Patterns
- Use `UnifiedHttpClient` for HTTP
- Use credential providers for secrets
- Implement retry/circuit breaker
- Handle rate limiting

## Outputs
- Integration adapters
- Configuration schemas
- Error handling
- Tests with mocks
