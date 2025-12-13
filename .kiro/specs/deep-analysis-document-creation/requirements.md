# Deep Analysis Document Creation Requirements

## Introduction

This specification addresses the issue where clicking the "start analyze" button should immediately create a new document containing the overall score and old data from the quick scan, but this document is not appearing as expected.

## Glossary

- **Deep Analysis**: Stage 2 analysis that provides detailed ACID scores and overall assessment
- **Quick Scan Document**: The original document created during the initial repository scan
- **Analysis Results Document**: A new document created when deep analysis starts, containing both old data and new analysis results
- **Document Type**: A field that identifies the purpose and type of each document in the database
- **Overall Score**: The calculated score from deep analysis (e.g., 88.5, 91.2)

## Requirements

### Requirement 1

**User Story:** As a user, I want a new document to be created immediately when I click "start analyze", so that I can see the analysis results with the overall score and all my original data preserved.

#### Acceptance Criteria

1. WHEN a user clicks the "start analyze" button THEN the system SHALL immediately create a new document with document_type 'updated_with_deep_analysis'
2. WHEN the new document is created THEN the system SHALL copy all data from the most recent quick scan document
3. WHEN copying data THEN the system SHALL preserve all repository information, user profile data, and metadata from the original document
4. WHEN creating the new document THEN the system SHALL add the overall score field with the calculated deep analysis score
5. WHEN the document is created THEN the system SHALL set deepAnalysisComplete to true and needsDeepAnalysis to false

### Requirement 2

**User Story:** As a user, I want the new analysis document to be immediately accessible, so that I can see my results without waiting for background processing to complete.

#### Acceptance Criteria

1. WHEN the deep analysis starts THEN the system SHALL create the new document synchronously before starting background analysis
2. WHEN the document is created THEN the system SHALL return the document ID and confirmation in the API response
3. WHEN querying for results THEN the system SHALL prioritize the 'updated_with_deep_analysis' document type over regular scan documents
4. WHEN multiple analysis documents exist THEN the system SHALL return the most recent one based on scan_date
5. WHEN the document is created THEN the system SHALL include a unique analysis_id for tracking

### Requirement 3

**User Story:** As a developer, I want the document creation to be integrated into the main analysis workflow, so that it happens reliably every time deep analysis is initiated.

#### Acceptance Criteria

1. WHEN deep analysis is initiated through any endpoint THEN the system SHALL create the new document as part of the main workflow
2. WHEN document creation fails THEN the system SHALL return an error and not proceed with analysis
3. WHEN the document is created THEN the system SHALL log the creation with document ID and score information
4. WHEN background analysis completes THEN the system SHALL update the existing document rather than create a new one
5. WHEN multiple users initiate analysis THEN the system SHALL create separate documents with unique identifiers

### Requirement 4

**User Story:** As a user, I want the enhanced quick scan endpoint to return my analysis results, so that I can see the overall score and detailed analysis data.

#### Acceptance Criteria

1. WHEN calling the enhanced quick scan endpoint THEN the system SHALL return the latest analysis document if it exists
2. WHEN no analysis document exists THEN the system SHALL return the regular quick scan document
3. WHEN returning analysis data THEN the system SHALL include the overall score, detailed scores, and analysis metadata
4. WHEN the document has deep analysis results THEN the system SHALL set hasDeepAnalysis to true in the response
5. WHEN formatting the response THEN the system SHALL maintain compatibility with existing frontend expectations

### Requirement 5

**User Story:** As a system administrator, I want proper error handling and logging for document creation, so that I can troubleshoot issues when they occur.

#### Acceptance Criteria

1. WHEN document creation fails THEN the system SHALL log detailed error information including username and database details
2. WHEN the source document is not found THEN the system SHALL return a 404 error with a descriptive message
3. WHEN database operations fail THEN the system SHALL return a 500 error and log the database error details
4. WHEN successful THEN the system SHALL log the document creation with all relevant metadata
5. WHEN debugging is needed THEN the system SHALL provide debug endpoints to inspect document states