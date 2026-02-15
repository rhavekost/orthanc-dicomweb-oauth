# Test Coverage Improvement Plan

**Goal**: Increase test coverage from 82.88% to 90%+ and fix pylint score

**Current Status**:
- Overall coverage: 82.88%
- Codecov failing: Recent diff only 49.61% covered (target 85.65%)
- Pylint score: 8.96/10 (needs >= 9.0/10)

**Root Cause**: Recent refactoring extracted helper functions in `dicomweb_oauth_plugin.py` that lack test coverage.

## Tasks

### Task 1: Add tests for dicomweb_oauth_plugin.py helper functions (PRIORITY)

**Current coverage**: 62.05% (115/303 lines uncovered)

**Missing coverage** (lines from coverage report):
- Lines 98-103: Flask app creation error handling
- Lines 163-166: REST endpoint registration
- Lines 240-254: Helper function `_extract_server_name`
- Lines 270-274: Helper function `_get_stow_url`
- Lines 332, 347-370: Helper functions `_get_oauth_token`, `_prepare_json_request`
- Lines 434-438: Helper function `_prepare_request_body_and_headers`
- Lines 457-461: Helper function `_send_dicom_to_server`
- Lines 496-499: Helper function `_process_stow_request`

**Required tests**:
1. Test `_extract_server_name` with valid/invalid URIs
2. Test `_get_stow_url` with configured/unconfigured servers
3. Test `_get_oauth_token` with successful/failed token acquisition
4. Test `_prepare_json_request` with valid JSON body containing resource IDs
5. Test `_prepare_request_body_and_headers` for multipart vs JSON content types
6. Test `_send_dicom_to_server` with various HTTP response codes (200, 409, 500)
7. Test `_process_stow_request` end-to-end integration
8. Test Flask app creation error handling when dependencies missing

**Implementation**:
- Create new test file: `tests/test_dicomweb_plugin_helpers.py`
- Use existing mocking patterns from `test_transparent_oauth_proxy.py`
- Test both success and error paths for each helper
- Target: 95%+ coverage for this file

### Task 2: Improve OAuth provider coverage

**Files needing coverage**:
- `src/oauth_providers/aws.py`: 55.56% → 90%+ (lines 31, 41-58)
- `src/oauth_providers/google.py`: 52.00% → 90%+ (lines 22, 37-54)
- `src/oauth_providers/azure.py`: 68.97% → 90%+ (lines 39-43, 65-77, 96)
- `src/oauth_providers/generic.py`: 74.55% → 90%+ (lines 109, 150-209)

**Required tests**:
1. AWS provider: Test STS token acquisition, region configuration, error handling
2. Google provider: Test service account JWT flow, scope validation
3. Azure provider: Test Entra ID token acquisition, JWKS validation (currently stubbed)
4. Generic provider: Test custom token endpoint, refresh flow, error responses

**Implementation**:
- Enhance existing test files: `test_aws_provider.py`, `test_google_provider.py`
- Add new tests for error paths and edge cases
- Mock HTTP responses for token endpoints

### Task 3: Improve cache and rate limiter coverage

**Files needing coverage**:
- `src/cache/base.py`: 72.22% → 95%+ (lines 24, 38, 50, 62, 71)
- `src/cache/redis_cache.py`: 76.74% → 90%+ (lines 61-62, 74-75, 81-82, 88-89, 99-100)
- `src/rate_limiter.py`: 73.68% → 90%+ (lines 94-96, 108-118)

**Required tests**:
1. Cache base: Test abstract methods raise NotImplementedError
2. Redis cache: Test connection errors, Redis unavailable scenarios
3. Rate limiter: Test cleanup of expired windows, concurrent access

**Implementation**:
- Add error path tests to existing test files
- Mock Redis connection failures
- Test thread safety for rate limiter

### Task 4: Fix pylint score (8.96 → 9.0+)

**Current score**: 8.96/10

**Likely issues**:
- New helper functions may have pylint warnings
- Check for: missing docstrings, too many arguments, complexity

**Implementation**:
- Run `pylint src/dicomweb_oauth_plugin.py --rcfile=pyproject.toml`
- Fix identified issues
- Verify score improves to 9.0+

## Success Criteria

- [ ] Overall test coverage >= 90%
- [ ] Codecov patch coverage >= 85.65%
- [ ] dicomweb_oauth_plugin.py coverage >= 95%
- [ ] All OAuth providers coverage >= 90%
- [ ] Pylint score >= 9.0/10
- [ ] All tests passing
- [ ] Pre-commit hooks passing

## Execution Order

1. Task 1 (highest impact - fixes codecov failure)
2. Task 4 (quick fix)
3. Task 2 (medium coverage files)
4. Task 3 (lower priority)

## Context

- Recent refactoring (commit dc0348d) extracted 8 helper functions from `handle_rest_api_stow`
- These helpers reduced complexity from 14 → 3 but lack test coverage
- Existing transparent OAuth tests in `test_transparent_oauth_proxy.py` test the high-level flow
- Need granular unit tests for each helper function
