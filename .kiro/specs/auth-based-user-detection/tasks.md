# Implementation Plan

## Overview
This implementation plan focuses on making minimal changes to replace whitelist-based user detection with pure JWT authentication-based detection. All existing functionality remains unchanged.

## Tasks

- [x] 1. Remove whitelist from UserTypeDetector


  - Remove `INTERNAL_USER_WHITELIST` constant from `backend/app/user_type_detector.py`
  - Update class docstring to reflect authentication-based detection
  - _Requirements: 4.1, 4.4_

- [x] 2. Simplify detect_user_type method


  - Remove all whitelist checking logic from `detect_user_type()` method
  - Simplify method to only check JWT token presence via `get_current_user_optional()`
  - Update method docstring and comments
  - _Requirements: 1.3, 2.2, 4.2, 4.3_

- [ ]* 2.1 Write property test for JWT-based classification
  - **Property 1: JWT-based user type classification**
  - **Validates: Requirements 1.3, 2.2**

- [ ]* 2.2 Write property test for username independence
  - **Property 5: Username independence for authenticated users**
  - **Property 6: Username independence for unauthenticated users**  
  - **Validates: Requirements 4.2, 4.3**

- [x] 3. Update logging messages


  - Ensure log messages reflect authentication-based detection
  - Remove any references to whitelist in log messages
  - _Requirements: 1.5, 2.5_

- [ ]* 3.1 Write property test for log marker consistency
  - **Property 9: Log marker consistency**
  - **Validates: Requirements 1.5, 2.5**

- [x] 4. Verify existing functionality unchanged


  - Test that all existing endpoints work exactly the same
  - Verify database routing still works correctly
  - Confirm user ID generation and collection naming unchanged
  - _Requirements: 3.4, 3.5_

- [ ]* 4.1 Write property test for database routing consistency
  - **Property 2: Database routing by user type**
  - **Validates: Requirements 1.4, 2.3**

- [ ]* 4.2 Write property test for user ID and collection naming
  - **Property 3: User ID prefix consistency**
  - **Property 4: Collection naming by user type**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ]* 4.3 Write property test for functionality preservation
  - **Property 7: Existing functionality preservation**
  - **Validates: Requirements 3.4, 3.5**

- [x] 5. Test with real scenarios





  - Test authenticated user (with JWT) gets classified as internal
  - Test unauthenticated user (no JWT) gets classified as external
  - Verify `raseen2305` now gets classified based on JWT presence, not whitelist
  - _Requirements: 1.3, 2.2, 4.1_

- [x] 6. Checkpoint - Ensure all tests pass




  - Ensure all tests pass, ask the user if questions arise.