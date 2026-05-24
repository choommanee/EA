# Design Document

## Overview

This design addresses critical issues in the FVG Trading EA that are causing abnormal trading behavior. The main problems identified are:

1. **Exponential lot size growth**: The current grid system multiplies total existing lots by the multiplier, causing exponential growth (1 → 1.2 → 2.4 → 4.8 → 9.6 → 19.2 → 38.4 → 76.8 → 153.6 lots)
2. **Lack of duplicate order prevention**: No mechanism prevents multiple orders from being placed simultaneously
3. **Conflicting grid logic**: Both buy and sell grids can be active simultaneously
4. **Missing lot size validation**: No proper validation against account balance and broker limits
5. **Poor state management**: Grid state variables are not properly synchronized

## Architecture

The solution will implement a layered approach with clear separation of concerns:

```
┌─────────────────────────────────────┐
│           Trading Controller        │
│  - Order validation and locking     │
│  - State management                 │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│         Risk Management Layer       │
│  - Lot size validation             │
│  - Account balance checks          │
│  - Maximum exposure limits         │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│         Grid Logic Controller       │
│  - Single direction enforcement     │
│  - Progressive lot calculation      │
│  - Grid level management           │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│         Order Execution Layer       │
│  - Atomic order placement          │
│  - Error handling and recovery     │
│  - Comprehensive logging           │
└─────────────────────────────────────┘
```

## Components and Interfaces

### 1. Trading State Manager

**Purpose**: Manage trading state and prevent concurrent operations

**Key Functions**:
- `bool AcquireTradingLock()` - Acquire exclusive trading lock
- `void ReleaseTradingLock()` - Release trading lock
- `bool IsOrderProcessing()` - Check if order is being processed
- `void UpdateGridState()` - Synchronize grid state variables

**State Variables**:
```mql5
bool g_trading_lock = false;
datetime g_last_order_time = 0;
int g_active_grid_direction = 0; // 1=Buy, -1=Sell, 0=None
```

### 2. Risk Management Controller

**Purpose**: Validate lot sizes and enforce risk limits

**Key Functions**:
- `double ValidateLotSize(double requested_lot)` - Validate and normalize lot size
- `bool CheckAccountRisk(double lot_size, double price)` - Check if trade fits risk parameters
- `double GetMaxAllowedLot()` - Calculate maximum allowed lot size based on account
- `bool CheckMaxExposure(double additional_lot)` - Check total exposure limits

**Risk Calculations**:
```mql5
// Maximum lot based on account balance and risk percentage
max_lot = (account_balance * risk_percent / 100) / (stop_loss_distance * tick_value)

// Maximum exposure check
total_exposure = current_positions_value + (new_lot * current_price * contract_size)
max_exposure = account_balance * max_exposure_percent / 100
```

### 3. Grid Logic Controller

**Purpose**: Implement correct grid trading logic with progressive scaling

**Key Functions**:
- `double CalculateNextGridLot(ENUM_ORDER_TYPE order_type)` - Calculate next grid level lot size
- `bool ShouldOpenGridLevel(ENUM_ORDER_TYPE order_type, double current_price)` - Determine if new grid level should open
- `void ResetGridDirection()` - Reset grid when changing direction
- `int GetCurrentGridLevel(ENUM_ORDER_TYPE order_type)` - Get current grid level

**Progressive Lot Calculation**:
```mql5
// Instead of: new_lot = total_existing_lots * multiplier
// Use: new_lot = base_lot * (multiplier ^ grid_level)
double CalculateProgressiveLot(int grid_level)
{
    double base_lot = InpFixedLotSize;
    double progressive_lot = base_lot * MathPow(InpGridMultiplier, grid_level);
    return ValidateLotSize(progressive_lot);
}
```

### 4. Order Execution Manager

**Purpose**: Handle atomic order placement with proper error handling

**Key Functions**:
- `bool ExecuteGridOrder(ENUM_ORDER_TYPE order_type, double lot_size, double price)` - Execute single grid order
- `void LogOrderExecution(string operation, double lot_size, double price, bool success)` - Comprehensive logging
- `bool ValidateOrderParameters(ENUM_ORDER_TYPE order_type, double lot_size, double price)` - Pre-execution validation

## Data Models

### Enhanced Grid State Structure
```mql5
struct GridState
{
    int direction;              // 1=Buy, -1=Sell, 0=None
    int current_level;          // Current grid level (0-based)
    double base_lot_size;       // Base lot size for calculations
    double total_volume;        // Total volume in current direction
    double average_price;       // Average entry price
    datetime last_order_time;   // Last order timestamp
    bool is_locked;            // Grid operation lock
};
```

### Risk Management State
```mql5
struct RiskState
{
    double max_lot_per_trade;   // Maximum lot per single trade
    double max_total_exposure;  // Maximum total exposure
    double current_exposure;    // Current total exposure
    double account_risk_amount; // Risk amount based on account balance
    bool risk_limits_exceeded;  // Risk limit status
};
```

## Error Handling

### 1. Lot Size Validation Errors
- **Invalid lot size**: Normalize to nearest valid lot size within broker limits
- **Excessive lot size**: Cap at maximum safe level based on account balance
- **Zero or negative lot**: Use minimum broker lot size

### 2. Duplicate Order Prevention
- **Concurrent order attempts**: Use atomic locking mechanism
- **Same timestamp orders**: Implement minimum time delay between orders
- **Grid level conflicts**: Validate grid level before execution

### 3. Grid Logic Errors
- **Direction conflicts**: Reset grid when changing direction
- **State synchronization**: Regularly update grid state from actual positions
- **Level calculation errors**: Recalculate grid levels from existing positions

### 4. Recovery Mechanisms
- **State corruption**: Rebuild grid state from existing positions
- **Lock timeout**: Automatic lock release after timeout period
- **Connection loss**: Re-synchronize state on reconnection

## Testing Strategy

### 1. Unit Tests
- **Lot size calculations**: Test progressive lot calculation with various multipliers
- **Risk validation**: Test lot size validation against different account balances
- **Grid level logic**: Test grid level calculations and direction changes
- **Lock mechanism**: Test concurrent access prevention

### 2. Integration Tests
- **Order execution flow**: Test complete order execution with all validations
- **State synchronization**: Test grid state updates after order execution
- **Error recovery**: Test recovery from various error conditions
- **Risk limit enforcement**: Test behavior when risk limits are reached

### 3. Scenario Tests
- **Normal grid operation**: Test progressive grid building in one direction
- **Direction change**: Test grid reset and new direction establishment
- **Account limit scenarios**: Test behavior with low account balance
- **High volatility**: Test rapid price movement scenarios

### 4. Performance Tests
- **High frequency mode**: Test performance with rapid order generation
- **Memory usage**: Test memory consumption with maximum grid levels
- **Lock contention**: Test performance under concurrent access attempts

## Implementation Phases

### Phase 1: Core Infrastructure
1. Implement trading state manager with locking mechanism
2. Create risk management controller with lot validation
3. Add comprehensive logging system
4. Implement basic error recovery

### Phase 2: Grid Logic Fixes
1. Fix progressive lot calculation algorithm
2. Implement single direction enforcement
3. Add proper grid level tracking
4. Create grid state synchronization

### Phase 3: Advanced Features
1. Add sophisticated risk management
2. Implement advanced error recovery
3. Add performance optimizations
4. Create comprehensive monitoring

### Phase 4: Testing and Validation
1. Implement comprehensive test suite
2. Perform stress testing
3. Validate against historical data
4. Performance optimization

## Security Considerations

1. **Input validation**: All user inputs and calculated values must be validated
2. **State integrity**: Grid state must be protected from corruption
3. **Resource limits**: Prevent excessive memory or CPU usage
4. **Error information**: Avoid exposing sensitive information in error messages

## Performance Considerations

1. **Lock efficiency**: Use lightweight locking mechanisms
2. **State updates**: Minimize frequency of state synchronization
3. **Logging optimization**: Use buffered logging for high-frequency operations
4. **Memory management**: Efficient array and structure management

## Monitoring and Observability

1. **Order execution metrics**: Track success/failure rates
2. **Risk limit monitoring**: Alert when approaching risk limits
3. **Grid performance**: Monitor grid profitability and drawdown
4. **System health**: Track lock contention and error rates