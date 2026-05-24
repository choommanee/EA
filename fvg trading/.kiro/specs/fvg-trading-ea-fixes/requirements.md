# Requirements Document

## Introduction

This specification addresses critical issues found in the FVG Trading EA that are causing abnormal trading behavior, including excessive lot sizes (100 lots), duplicate order execution, conflicting grid logic, and incorrect lot size calculations. The fixes will ensure proper risk management, prevent duplicate trades, and implement correct grid trading logic.

## Requirements

### Requirement 1: Volume Control and Risk Management

**User Story:** As a trader, I want the EA to use appropriate lot sizes based on my risk settings, so that I don't risk excessive capital on single trades.

#### Acceptance Criteria

1. WHEN calculating lot size THEN the system SHALL ensure maximum lot size does not exceed user-defined risk parameters
2. WHEN lot multiplier is applied THEN the system SHALL validate the resulting lot size against broker limits and account balance
3. IF calculated lot size exceeds maximum allowed THEN the system SHALL cap it at the maximum safe level
4. WHEN opening any position THEN the system SHALL log the lot size calculation for audit purposes

### Requirement 2: Duplicate Order Prevention

**User Story:** As a trader, I want the EA to prevent opening multiple orders at the same time, so that I don't have unintended position exposure.

#### Acceptance Criteria

1. WHEN checking for new trade opportunities THEN the system SHALL verify no pending orders exist for the same symbol and direction
2. WHEN an order is being processed THEN the system SHALL implement a lock mechanism to prevent concurrent order execution
3. IF multiple signals occur simultaneously THEN the system SHALL process only the first valid signal
4. WHEN order execution completes THEN the system SHALL update internal state before processing new signals

### Requirement 3: Grid Logic Correction

**User Story:** As a trader, I want the grid trading logic to work correctly without conflicting Buy and Sell orders, so that the strategy executes as intended.

#### Acceptance Criteria

1. WHEN grid logic is active THEN the system SHALL maintain only one direction (Buy OR Sell) per grid sequence
2. WHEN determining grid direction THEN the system SHALL use clear trend analysis to avoid conflicting signals
3. IF market conditions change THEN the system SHALL close existing grid before starting opposite direction
4. WHEN grid levels are calculated THEN the system SHALL ensure proper spacing and direction consistency

### Requirement 4: Lot Size Calculation Fix

**User Story:** As a trader, I want accurate lot size calculations that follow proper money management rules, so that my risk per trade is controlled and predictable.

#### Acceptance Criteria

1. WHEN calculating initial lot size THEN the system SHALL use account balance, risk percentage, and stop loss distance
2. WHEN applying lot multiplier for grid levels THEN the system SHALL use progressive scaling that respects maximum exposure limits
3. IF lot calculation results in invalid size THEN the system SHALL normalize to nearest valid lot size
4. WHEN lot size is determined THEN the system SHALL validate against broker minimum and maximum lot requirements

### Requirement 5: Order Execution Monitoring

**User Story:** As a trader, I want comprehensive logging and monitoring of order execution, so that I can identify and debug any issues quickly.

#### Acceptance Criteria

1. WHEN any order is placed THEN the system SHALL log timestamp, symbol, direction, lot size, and price
2. WHEN order execution fails THEN the system SHALL log error details and reason for failure
3. WHEN duplicate order attempt is detected THEN the system SHALL log the prevention action
4. WHEN lot size is adjusted THEN the system SHALL log original calculation and final adjusted value

### Requirement 6: State Management and Recovery

**User Story:** As a trader, I want the EA to maintain consistent internal state and recover properly from errors, so that trading continues reliably.

#### Acceptance Criteria

1. WHEN EA starts THEN the system SHALL initialize all state variables and verify existing positions
2. WHEN error occurs THEN the system SHALL reset relevant state variables to prevent cascading issues
3. IF connection is lost THEN the system SHALL re-synchronize state when connection is restored
4. WHEN EA is stopped and restarted THEN the system SHALL properly restore previous state and continue operations