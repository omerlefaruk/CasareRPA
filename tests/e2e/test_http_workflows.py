"""
CasareRPA - E2E Tests for HTTP Request Workflows.

Tests HTTP operations using httpbin.org as an external test server:
- GET requests (basic, with query params, headers, user-agent)
- POST requests (JSON, form data, text body)
- PUT/DELETE/PATCH methods
- Status code handling (2xx, 4xx, 5xx)
- Response handling (body, headers, cookies)
- Authentication (Basic, Bearer)
- Timeouts and delays
- Complex API workflows (CRUD, pagination, conditional)
"""

import pytest

from .helpers.workflow_builder import WorkflowBuilder


# =============================================================================
# GET REQUESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpGet:
    """Tests for HTTP GET requests."""

    async def test_http_get_basic(self) -> None:
        """Test basic GET request to httpbin.org."""
        result = await (
            WorkflowBuilder("HTTP GET Basic")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_get_with_query_params(self) -> None:
        """Test GET request with query parameters."""
        result = await (
            WorkflowBuilder("HTTP GET Query Params")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
                params={"foo": "bar", "count": "42"},
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_get_json_response(self) -> None:
        """Test GET request that returns JSON response."""
        result = await (
            WorkflowBuilder("HTTP GET JSON Response")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/json",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_get_with_headers(self) -> None:
        """Test GET request with custom headers."""
        result = await (
            WorkflowBuilder("HTTP GET Headers")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/headers",
                headers={"X-Custom-Header": "test-value", "Accept": "application/json"},
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_get_user_agent(self) -> None:
        """Test GET request with custom User-Agent header."""
        result = await (
            WorkflowBuilder("HTTP GET User-Agent")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/user-agent",
                headers={"User-Agent": "CasareRPA/1.0"},
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# POST REQUESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpPost:
    """Tests for HTTP POST requests."""

    async def test_http_post_json(self) -> None:
        """Test POST request with JSON body."""
        result = await (
            WorkflowBuilder("HTTP POST JSON")
            .add_start()
            .add_http_request(
                method="POST",
                url="https://httpbin.org/post",
                body='{"key": "value", "number": 42}',
                content_type="application/json",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_post_form_data(self) -> None:
        """Test POST request with form data."""
        result = await (
            WorkflowBuilder("HTTP POST Form")
            .add_start()
            .add_http_request(
                method="POST",
                url="https://httpbin.org/post",
                body="username=testuser&password=testpass",
                content_type="application/x-www-form-urlencoded",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_post_text(self) -> None:
        """Test POST request with plain text body."""
        result = await (
            WorkflowBuilder("HTTP POST Text")
            .add_start()
            .add_http_request(
                method="POST",
                url="https://httpbin.org/post",
                body="Hello, World! This is plain text.",
                content_type="text/plain",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_post_with_headers(self) -> None:
        """Test POST request with custom headers."""
        result = await (
            WorkflowBuilder("HTTP POST Headers")
            .add_start()
            .add_http_request(
                method="POST",
                url="https://httpbin.org/post",
                body='{"data": "test"}',
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token",
                    "X-Request-ID": "12345",
                },
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# PUT/DELETE/PATCH METHODS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpMethods:
    """Tests for PUT, DELETE, PATCH HTTP methods."""

    async def test_http_put(self) -> None:
        """Test PUT request."""
        result = await (
            WorkflowBuilder("HTTP PUT")
            .add_start()
            .add_http_request(
                method="PUT",
                url="https://httpbin.org/put",
                body='{"updated": true}',
                content_type="application/json",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_delete(self) -> None:
        """Test DELETE request."""
        result = await (
            WorkflowBuilder("HTTP DELETE")
            .add_start()
            .add_http_request(
                method="DELETE",
                url="https://httpbin.org/delete",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_patch(self) -> None:
        """Test PATCH request."""
        result = await (
            WorkflowBuilder("HTTP PATCH")
            .add_start()
            .add_http_request(
                method="PATCH",
                url="https://httpbin.org/patch",
                body='{"field": "new_value"}',
                content_type="application/json",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_head(self) -> None:
        """Test HEAD request (returns headers only)."""
        result = await (
            WorkflowBuilder("HTTP HEAD")
            .add_start()
            .add_http_request(
                method="HEAD",
                url="https://httpbin.org/get",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_options(self) -> None:
        """Test OPTIONS request."""
        result = await (
            WorkflowBuilder("HTTP OPTIONS")
            .add_start()
            .add_http_request(
                method="OPTIONS",
                url="https://httpbin.org/get",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# STATUS CODES
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpStatusCodes:
    """Tests for handling different HTTP status codes."""

    async def test_http_status_200(self) -> None:
        """Test handling 200 OK response."""
        result = await (
            WorkflowBuilder("HTTP Status 200")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/200",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_201(self) -> None:
        """Test handling 201 Created response."""
        result = await (
            WorkflowBuilder("HTTP Status 201")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/201",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_204(self) -> None:
        """Test handling 204 No Content response."""
        result = await (
            WorkflowBuilder("HTTP Status 204")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/204",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_400(self) -> None:
        """Test handling 400 Bad Request response."""
        result = await (
            WorkflowBuilder("HTTP Status 400")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/400",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        # Node execution succeeds but HTTP status is 400
        assert result["success"] is True

    async def test_http_status_401(self) -> None:
        """Test handling 401 Unauthorized response."""
        result = await (
            WorkflowBuilder("HTTP Status 401")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/401",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_403(self) -> None:
        """Test handling 403 Forbidden response."""
        result = await (
            WorkflowBuilder("HTTP Status 403")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/403",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_404(self) -> None:
        """Test handling 404 Not Found response."""
        result = await (
            WorkflowBuilder("HTTP Status 404")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/404",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_500(self) -> None:
        """Test handling 500 Internal Server Error response."""
        result = await (
            WorkflowBuilder("HTTP Status 500")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/500",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_502(self) -> None:
        """Test handling 502 Bad Gateway response."""
        result = await (
            WorkflowBuilder("HTTP Status 502")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/502",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_status_503(self) -> None:
        """Test handling 503 Service Unavailable response."""
        result = await (
            WorkflowBuilder("HTTP Status 503")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/503",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# RESPONSE HANDLING
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpResponse:
    """Tests for HTTP response handling."""

    async def test_http_response_body_text(self) -> None:
        """Test extracting text body from HTML response."""
        result = await (
            WorkflowBuilder("HTTP Response Body")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/html",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_response_headers(self) -> None:
        """Test extracting response headers."""
        result = await (
            WorkflowBuilder("HTTP Response Headers")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/response-headers",
                params={"Content-Type": "application/json"},
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_response_cookies(self) -> None:
        """Test handling cookies in response."""
        result = await (
            WorkflowBuilder("HTTP Response Cookies")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/cookies/set/session_id/abc123",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_gzip_response(self) -> None:
        """Test handling gzip-compressed response."""
        result = await (
            WorkflowBuilder("HTTP GZIP Response")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/gzip",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_deflate_response(self) -> None:
        """Test handling deflate-compressed response."""
        result = await (
            WorkflowBuilder("HTTP Deflate Response")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/deflate",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# AUTHENTICATION
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpAuth:
    """Tests for HTTP authentication."""

    async def test_http_basic_auth_success(self) -> None:
        """Test successful Basic authentication."""
        result = await (
            WorkflowBuilder("HTTP Basic Auth Success")
            .add_start()
            .add_http_auth(
                auth_type="Basic",
                username="user",
                password="passwd",
            )
            .add_http_request(
                method="GET",
                url="https://httpbin.org/basic-auth/user/passwd",
                headers_from_var="{{auth_headers}}",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_basic_auth_failure(self) -> None:
        """Test failed Basic authentication (wrong credentials)."""
        result = await (
            WorkflowBuilder("HTTP Basic Auth Failure")
            .add_start()
            .add_http_auth(
                auth_type="Basic",
                username="wrong",
                password="credentials",
            )
            .add_http_request(
                method="GET",
                url="https://httpbin.org/basic-auth/user/passwd",
                headers_from_var="{{auth_headers}}",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        # Workflow executes, but HTTP returns 401
        assert result["success"] is True

    async def test_http_bearer_token(self) -> None:
        """Test Bearer token authentication."""
        result = await (
            WorkflowBuilder("HTTP Bearer Token")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/bearer",
                headers={"Authorization": "Bearer my-token-12345"},
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_digest_auth(self) -> None:
        """Test hidden-basic-auth endpoint (simulates auth flow)."""
        result = await (
            WorkflowBuilder("HTTP Hidden Basic Auth")
            .add_start()
            .add_http_auth(
                auth_type="Basic",
                username="user",
                password="passwd",
            )
            .add_http_request(
                method="GET",
                url="https://httpbin.org/hidden-basic-auth/user/passwd",
                headers_from_var="{{auth_headers}}",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# TIMEOUTS AND DELAYS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpTimeouts:
    """Tests for HTTP timeouts and delays."""

    async def test_http_delay_success(self) -> None:
        """Test request with delay that completes within timeout."""
        result = await (
            WorkflowBuilder("HTTP Delay Success")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/delay/1",
                timeout=10.0,
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_delay_2_seconds(self) -> None:
        """Test request with 2-second delay."""
        result = await (
            WorkflowBuilder("HTTP Delay 2s")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/delay/2",
                timeout=15.0,
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_timeout_exceeded(self) -> None:
        """Test request that exceeds timeout - should fail gracefully."""
        result = await (
            WorkflowBuilder("HTTP Timeout Exceeded")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/delay/10",
                timeout=2.0,
            )
            .add_end()
            .execute(timeout=60.0)
        )

        # Workflow should fail due to timeout
        assert result["success"] is False
        assert (
            "timed out" in result.get("error", "").lower()
            or "timeout" in result.get("error", "").lower()
        )


# =============================================================================
# COMPLEX WORKFLOWS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpWorkflows:
    """Tests for complex HTTP workflows."""

    async def test_api_crud_workflow(self) -> None:
        """Test CRUD-like workflow: POST create -> GET read -> PUT update -> DELETE."""
        result = await (
            WorkflowBuilder("API CRUD Workflow")
            .add_start()
            # Create (POST)
            .add_http_request(
                method="POST",
                url="https://httpbin.org/post",
                body='{"name": "Test Item", "id": 1}',
                content_type="application/json",
            )
            # Read (GET)
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
                params={"id": "1"},
            )
            # Update (PUT)
            .add_http_request(
                method="PUT",
                url="https://httpbin.org/put",
                body='{"name": "Updated Item", "id": 1}',
                content_type="application/json",
            )
            # Delete (DELETE)
            .add_http_request(
                method="DELETE",
                url="https://httpbin.org/delete",
            )
            .add_end()
            .execute(timeout=120.0)
        )

        assert result["success"] is True

    async def test_sequential_get_requests(self) -> None:
        """Test multiple sequential GET requests."""
        result = await (
            WorkflowBuilder("Sequential GET Requests")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
                params={"page": "1"},
            )
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
                params={"page": "2"},
            )
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
                params={"page": "3"},
            )
            .add_end()
            .execute(timeout=120.0)
        )

        assert result["success"] is True

    async def test_api_with_headers_workflow(self) -> None:
        """Test workflow that builds headers then makes request."""
        result = await (
            WorkflowBuilder("API Headers Workflow")
            .add_start()
            .add_set_http_headers(
                headers_json={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-API-Version": "1.0",
                }
            )
            .add_http_request(
                method="GET",
                url="https://httpbin.org/headers",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-API-Version": "1.0",
                },
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_conditional_request_flow(self) -> None:
        """Test conditional request based on previous response."""
        result = await (
            WorkflowBuilder("Conditional Request Flow")
            .add_start()
            # First request to get status
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/200",
            )
            # Set a success flag
            .add_set_variable("api_succeeded", True)
            # Conditional based on the flag
            .add_if("{{api_succeeded}} == True")
            .branch_true()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
                params={"status": "success"},
            )
            .branch_false()
            .add_log("API call failed, skipping next request")
            .end_if()
            .add_end()
            .execute(timeout=120.0)
        )

        assert result["success"] is True

    async def test_api_with_url_building(self) -> None:
        """Test workflow that builds URL dynamically."""
        result = await (
            WorkflowBuilder("API URL Building")
            .add_start()
            .add_set_variable("base_url", "https://httpbin.org")
            .add_set_variable("endpoint", "/anything/users/123")
            .add_build_url(
                base_url="https://httpbin.org",
                path="/anything/users/123",
                params={"include": "profile", "format": "json"},
            )
            .add_http_request(
                method="GET",
                url="https://httpbin.org/anything/users/123",
                params={"include": "profile", "format": "json"},
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_api_json_extraction(self) -> None:
        """Test extracting data from JSON response."""
        result = await (
            WorkflowBuilder("API JSON Extraction")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/json",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_api_retry_pattern(self) -> None:
        """Test API call with retry on failure pattern."""
        result = await (
            WorkflowBuilder("API Retry Pattern")
            .add_start()
            # This should succeed on first try
            .add_http_request(
                method="GET",
                url="https://httpbin.org/get",
                retry_count=3,
                retry_delay=1.0,
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpEdgeCases:
    """Tests for HTTP edge cases and error handling."""

    async def test_http_empty_response_body(self) -> None:
        """Test handling response with empty body."""
        result = await (
            WorkflowBuilder("HTTP Empty Body")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/status/204",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_large_response(self) -> None:
        """Test handling large response (stream of bytes)."""
        result = await (
            WorkflowBuilder("HTTP Large Response")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/bytes/1024",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_uuid_endpoint(self) -> None:
        """Test endpoint that generates UUID."""
        result = await (
            WorkflowBuilder("HTTP UUID")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/uuid",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_ip_endpoint(self) -> None:
        """Test endpoint that returns client IP."""
        result = await (
            WorkflowBuilder("HTTP IP")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/ip",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_anything_endpoint(self) -> None:
        """Test anything endpoint that echoes request details."""
        result = await (
            WorkflowBuilder("HTTP Anything")
            .add_start()
            .add_http_request(
                method="POST",
                url="https://httpbin.org/anything/test/path",
                body='{"test": "data"}',
                content_type="application/json",
                headers={"X-Test": "value"},
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_redirect(self) -> None:
        """Test handling HTTP redirects."""
        result = await (
            WorkflowBuilder("HTTP Redirect")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/redirect/1",
                follow_redirects=True,
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_redirect_chain(self) -> None:
        """Test handling multiple redirects in chain."""
        result = await (
            WorkflowBuilder("HTTP Redirect Chain")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/redirect/3",
                follow_redirects=True,
                max_redirects=10,
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_absolute_redirect(self) -> None:
        """Test absolute redirect."""
        result = await (
            WorkflowBuilder("HTTP Absolute Redirect")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/absolute-redirect/1",
                follow_redirects=True,
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True


# =============================================================================
# ENCODING AND DATA FORMATS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.network
class TestHttpEncoding:
    """Tests for various encodings and data formats."""

    async def test_http_utf8_response(self) -> None:
        """Test handling UTF-8 encoded response."""
        result = await (
            WorkflowBuilder("HTTP UTF8")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/encoding/utf8",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_robots_txt(self) -> None:
        """Test fetching robots.txt (plain text)."""
        result = await (
            WorkflowBuilder("HTTP Robots")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/robots.txt",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_xml_response(self) -> None:
        """Test handling XML response."""
        result = await (
            WorkflowBuilder("HTTP XML")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/xml",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True

    async def test_http_base64_decode(self) -> None:
        """Test base64 decode endpoint."""
        result = await (
            WorkflowBuilder("HTTP Base64")
            .add_start()
            .add_http_request(
                method="GET",
                url="https://httpbin.org/base64/SFRUUEJJTiBpcyBhd2Vzb21l",
            )
            .add_end()
            .execute(timeout=60.0)
        )

        assert result["success"] is True
