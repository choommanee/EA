# EA Project Memory

Last updated: 2026-05-24
Timezone: Asia/Bangkok

## User Goal

Build a new MetaTrader 5 EA that is easier to backtest and maintain than the combined `PSS_V6_Ultimate_EA.mq5`.

The desired EA is a focused Martingale system that uses SMC/SMS trend logic for direction and entries. Entries and add-orders should be based on market structure, not fixed price spacing alone.

Core entry concepts requested:

- BOS
- CHoCH
- Liquidity sweep / LQ
- Order Block / OB
- Optional FVG support
- Trend direction from SMC/SMS
- Martingale/grid recovery only when the structure gate allows it

Important: Do not promise guaranteed profit. The target is to reduce catastrophic tail risk and make the system testable.

## Main Working Paths

MetaTrader Experts folder:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts`

Python trade folder:

`C:\Users\User\OneDrive\เอกสาร\python-trade`

Current workspace:

`C:\Users\User\OneDrive\เอกสาร\Ea`

## Current New EA

Standalone EA created:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\PSS_SMC_Martingale_EA.mq5`

Compiled output:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\PSS_SMC_Martingale_EA.ex5`

Compile log:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\pss_smc_martingale_compile.log`

Latest known compile result:

- 0 errors
- 0 warnings

## New EA Design

`PSS_SMC_Martingale_EA.mq5` is separated from the large combined PSS EA to make backtests faster and config simpler.

Main systems included:

- Standalone SMC/SMS Martingale only
- No grid/momentum/multi-bot modules from the old combined EA
- Chart status panel
- Backtest decision logging with `PSSDBG` tags
- Trading-time filter with timezone offset
- Optional close basket outside allowed trading time
- Daily profit/loss guard
- Max drawdown guard
- Daily high/low guard
- Close retry logic when market close or trade context blocks immediate exit
- Runaway trend guard for strong one-way trends
- Optional runaway hedge mode
- Linear lot increment mode similar to Killer
- Multiplier lot mode as alternative

Current important defaults:

- `InpMagic=777771`
- `InpDebugLog=true`
- `InpLogStateEachBar=true`
- `InpLogOnlyChanges=true`
- `InpEntryMode=ENTRY_KILLER_MA_GRID`
- `InpLotMode=LOT_LINEAR_INCREMENT`
- `InpBaseLot=0.03`
- `InpLotIncrement=0.01`
- `InpMaxLevel=18`
- `InpMaxTotalLot=2.00`
- `InpProfitPer001Lot=0.10`
- `InpScaleTPByLot=true`
- `InpMinCloseProfitUSD=0.30`
- `InpUseProfitLock=true`
- `InpProfitLockStartUSD=0.30`
- `InpProfitLockRetraceUSD=0.10`
- `InpProfitLockMinUSD=0.05`
- `InpMaxDrawdownPercent=12.0`
- `InpUseRunawayGuard=true`
- `InpRunawayAction=RUNAWAY_CLOSE_BASKET`
- `InpRunawayMaPeriod=60`
- `InpRunawayAdxPeriod=14`
- `InpRunawayAdxLevel=32.0`
- `InpRunawayDistancePips=180`
- `InpRunawayLossPct=6.0`
- `InpRunawayMinLevel=3`

## Debug Log Format

The new EA prints decision logs to Strategy Tester Journal using the prefix `PSSDBG`.

Useful tags:

- `PSSDBG|INIT` for startup settings.
- `PSSDBG|STATE` once per bar with basket, P/L, equity, SMC object counts, and target profit.
- `PSSDBG|GATE` for SMC entry/add pass or wait reasons.
- `PSSDBG|MART` for Martingale hold reasons, such as waiting for adverse distance or max level reached.
- `PSSDBG|ORDER` for open order send result and trade server retcode.
- `PSSDBG|CLOSE` for basket close attempts and retcodes.
- `PSSDBG|RISK` for daily loss/profit or drawdown guards.
- `PSSDBG|RUNAWAY` for strong trend escape logic.
- `PSSDBG|TIME` for timezone/session blocks.
- `PSSDBG|TP` for basket profit close.

When reading a backtest log, search for `PSSDBG` first, then filter by tag.

## Current Direction After User Feedback

User clarified that the old Killer-style system did not mainly suffer from weak entries. Its major issue was a bug/behavior where the basket did not exit after floating profit appeared, then price ran back into loss. User then requested "ทำตามตัวเดิม" / follow the old EA behavior.

Adjustment made after this feedback:

- New EA default entry mode changed to `ENTRY_KILLER_MA_GRID`.
- L1 direction now follows MA60 bias, inferred from Killer report input `MA_Period=60`.
- Add-orders in Killer mode no longer require CHoCH/LQ/OB gate, so behavior is closer to the old grid/martingale EA.
- Default `InpBaseLot` changed to `0.03`, matching Killer `StartLot=0.03`.
- Default `InpMaxLevel` changed to `18` and `InpMaxTotalLot` to `2.00`, closer to old multi-level behavior but still capped below Killer's dangerous `MaxPositionSize=200`.
- `InpUseDailyHLGuard` changed to `false` by default so it does not block old-style entries.
- Strict mode remains available as `ENTRY_STRICT_SMC`.
- Balanced mode remains available as `ENTRY_BALANCED_SMC`.
- `InpMinCloseProfitUSD` reduced from `1.00` to `0.30`.
- Profit-lock system added: when floating basket profit reaches the lock threshold and then retraces, it closes while still positive.
- Profit close logs now include peak profit and close reason under `PSSDBG|TP`.

## Tester Set Note

On 2026-05-24, user showed a Strategy Tester visualization where the panel still displayed:

- `Gate: wait CHoCH+BOS`
- `Lot: 0.00 / 0.50`
- `Target: $1.00`

This proved the tester was using an old `.set` file, not the latest Killer-style defaults. The stale set was:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Profiles\Tester\PSS_SMC_Martingale_EA.set`

It was updated to:

- `InpEntryMode=0` / `ENTRY_KILLER_MA_GRID`
- `InpBaseLot=0.03`
- `InpMaxLevel=18`
- `InpMaxTotalLot=2.0`
- `InpMinCloseProfitUSD=0.3`
- `InpUseProfitLock=true`
- `InpUseDailyHLGuard=false`

If a future tester run still shows `wait CHoCH+BOS`, the tester is still loading old inputs or an older `.ex5`.

## Latest Log Finding

On 2026-05-24, agent log showed the latest run was correctly using:

- `entryMode=KILLER_MA_GRID`
- `baseLot=0.03`
- `maxTotalLot=2.00`
- `minCloseProfit=0.30`

The loss problem was not "not trading" anymore. It was caused by `InpDailyLossLimit=50.0` with `InpCloseOnDailyLoss=true`, which closed baskets too early around level 4-5 before Martingale recovery had time to work.

Examples from log:

- 2025-05-28 02:06:33: daily loss close at `pos=4`, `lots=0.18`, `pl=-56.98`.
- 2025-05-29 01:07:27: daily loss close at `pos=4`, `lots=0.18`, `pl=-51.15`.
- 2025-05-30 04:27:38: daily loss close at `pos=5`, `lots=0.25`, `pl=-83.98`.

Adjustment made:

- `InpDailyLossLimit=1000.0`
- `InpCloseOnDailyLoss=false`
- `InpRunawayDistancePips=120`
- `InpRunawayLossPct=2.0`
- `InpRunawayMinLevel=5`

Both `.mq5` and `.set` were updated, and the EA compiled with 0 errors / 0 warnings.

## Profit Exit Fix

User observed visually that baskets became profitable but the EA did not close; then price pulled back until the old daily loss guard closed around `-$50`. The cause was that the target profit could be too slow, especially with `InpScaleTPByLot=true`.

Adjustment made:

- `InpScaleTPByLot=false`
- `InpCloseAnyPositiveBasket=true`
- `InpAnyPositiveFromLevel=2`
- `InpAnyPositiveProfitUSD=0.05`
- `InpProfitLockStartUSD=0.05`
- `InpProfitLockRetraceUSD=0.02`
- `InpProfitLockMinUSD=0.00`
- Profit close check moved before risk guard inside `RunSmcMartingale()`.

Meaning: from level 2 upward, if the recovered basket is green by at least `$0.05`, close immediately. Do not wait for a larger scaled target.

User then clarified the EA still allowed small positive baskets to return to loss. Stronger adjustment made:

- `InpMinCloseProfitUSD=0.05`
- `InpAnyPositiveFromLevel=1`
- `InpAnyPositiveProfitUSD=0.01`
- `InpProfitLockStartUSD=0.01`
- `InpProfitLockRetraceUSD=0.01`
- Basket P/L calculation now includes `posInfo.Commission()` in addition to profit and swap.

Meaning: any level, including L1, closes as soon as net basket profit is at least `$0.01`. Profit check remains before risk guard.

## Exit Logic Reverted To PSS V6 Style

User later clarified that exiting for tiny profit is not economically useful and asked to reuse the exit method from `PSS_V6_Ultimate_EA.mq5`.

PSS V6 Martingale exit behavior found:

- `InpMartTakeProfitUSD=5.0`
- `InpMartTPScaling=false`
- `InpMartMinProfitUSD=1.0`
- Calculate a TP price from basket average price, total lot, tick value, and target profit.
- Close when total basket profit reaches the dollar target.
- Backup close when market price passes the calculated TP price and basket profit is above minimum profit.
- Keep retrying close if TP triggered but close failed.

New standalone EA updated to match this idea:

- `InpProfitPer001Lot=5.00` now acts as basket TP dollars when scaling is off.
- `InpScaleTPByLot=false`
- `InpMinCloseProfitUSD=1.00`
- `InpUseV6PriceTP=true`
- `InpCloseAnyPositiveBasket=false`
- `InpUseProfitLock=false`
- Added `CalculateV6TPPrice()`.
- `ShouldCloseBasketForProfit()` now uses `V6 dollar TP` and `V6 price TP` reasons.
- Panel target row can show target and calculated TP price.
- `.set` file updated to these values.

The earlier `$0.01 green close` logic remains available via inputs, but is disabled by default.

## Correction After User Feedback

User clarified that we should not change the old EA entry/open-order behavior. The original profitable behavior should remain; only the profit-close bug should be addressed.

Correction applied to `PSS_V6_Ultimate_EA.mq5`:

- `InpMartStrictSmcEntry=false`
- `InpMartAllowFallbackAdd=true`
- `InpMartStopAddOnOppositeBos=false`
- `InpMartUseDailyHLGuard=false`
- Martingale add-orders now bypass strict SMC gate when `InpMartStrictSmcEntry=false` and can add based on adverse distance again.
- `PSS_V6_Ultimate_EA.set` was updated with the same values so Strategy Tester does not reload stale strict settings.
- Recompiled `PSS_V6_Ultimate_EA.mq5` successfully with 0 errors / 0 warnings.

Important going forward: do not modify PSS V6 entry/open-order rules unless explicitly requested. Focus only on the close-profit bug and close retry behavior.

## Older Combined EA

Original file:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\PSS_V6_Ultimate_EA.mq5`

This EA had many systems combined, making configuration and backtesting slow.

It was patched earlier with stricter SMC Martingale logic:

- strict SMC entry gate
- CHoCH + BOS sequence
- liquidity sweep check
- OB zone check
- daily high/low guard
- opposite BOS stop-add guard

Known compile result after patch:

- 0 errors
- 0 warnings

But the user prefers a separated EA now.

## Killer Hunter Context

Existing old EA file:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\killer Hunter.ex5`

No source `.mq5` found. Do not help decompile or decode `.ex5`. Analyze behavior from reports, set files, and backtest logs only.

User provided report:

`C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\ReportTester-1114386.html`

This report is for `killer Hunter`, not PSS.

## Killer Hunter Backtest Findings

Report settings:

- Expert: `killer Hunter`
- Symbol: `XAUUSD-VIP`
- Timeframe: M3
- Initial deposit: 30,000
- Leverage: 1:500
- History quality: 99%
- `MagicNumber=12345`
- `StartLot=0.03`
- `MaxLot=500.0`
- `LotIncrement=0.01`
- `ProfitPer001Lot=0.1`
- `MA_Period=60`
- `MaxPositionSize=200.0`

Performance:

- Total net profit: -29,883.65
- Profit factor: 0.72
- Expected payoff: -1.40
- Balance drawdown maximal: 46,591.99 / 99.75%
- Equity drawdown maximal: 41,022.19 / 99.72%
- Recovery factor: -0.73
- Sharpe ratio: -2.41
- Total trades: 21,295
- Profit trades: 16,483 / 77.40%
- Loss trades: 4,812 / 22.60%
- Average profit trade: 4.64
- Average loss trade: -22.09
- Maximum consecutive losses: 43 / -41,022.19

Interpretation:

Killer Hunter wins often with small scalps, but its average loss is much larger than average profit. The system eventually fails during strong one-way trends because it keeps adding into a losing basket.

Major failure sequence:

- Around 2025-06-23 21:15 it started a trapped `BuyGrid` near price 3386.
- Price kept dropping toward 3300.
- It continued adding buy positions with linear lots from about 0.03 up to about 0.45.
- On 2025-06-24 16:39 many trades closed with stop-out comment `so 1.69%`.
- Final balance was reduced to roughly 116.35.

Main weakness:

No effective runaway-trend escape. It needs a hard rule to stop adding, close basket, or hedge when trend strength and floating loss exceed limits.

## Design Lessons From Killer Hunter

Good ideas to preserve:

- Simple linear lot increment
- Small profit target per 0.01 lot
- Dashboard/panel concept
- Fast scalping behavior

Dangerous parts to avoid:

- Huge `MaxLot`
- Huge `MaxPositionSize`
- Too many Martingale levels
- Adding against a strong one-way trend
- No basket age limit
- No hard escape before stop-out

## Recommended Next Improvements

High-priority additions to the new EA:

- Add basket age guard, for example close/hedge/stop-add after basket is open too long.
- Backtest the exact Killer failure window: XAUUSD-VIP M3, 2025-06-23 to 2025-06-25.
- Compare whether the new EA avoids the trapped BUY sequence or exits before stop-out.
- Add optional partial close / profit lock if backtests show baskets often become briefly recoverable.
- Tune `InpRunawayDistancePips`, `InpRunawayLossPct`, and `InpMaxLevel` using failure-window backtests.

Safer Killer-like starting config:

- `InpBaseLot=0.03`
- `InpLotMode=LOT_LINEAR_INCREMENT`
- `InpLotIncrement=0.01`
- `InpProfitPer001Lot=0.10`
- Keep `InpMaxTotalLot` limited, such as 0.50 to 1.00 for first tests.
- Keep `InpRunawayAction=RUNAWAY_CLOSE_BASKET` for safety testing.

## Compile Command

Use MetaEditor:

```powershell
& "C:\Program Files\MetaTrader 5\MetaEditor64.exe" /compile:"C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\PSS_SMC_Martingale_EA.mq5" /log:"C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\9BB124B7D418C7FB69DF2865535BA9BF\MQL5\Experts\pss_smc_martingale_compile.log"
```

## Communication Notes

User prefers Thai.

Be direct and practical. The user wants implementation, not only theory.

When discussing EA profitability, clearly say that profitability must be proven by backtest and forward test. Do not guarantee profit.

## Martingale Recovery Principle From User

For this project, do not treat cut loss as the main answer to martingale DD. The user's intended martingale principle is:

- A forced close at loss means the martingale cycle has already failed.
- The priority is better recovery entries, not surrendering the basket.
- Pip distance is only a minimum throttle; it must not be the full add-entry reason for deeper levels.
- From L4 onward, add entries should wait for real SMC/SMS timing such as OB, FVG, liquidity sweep, BOS, CHoCH, or clear trend exhaustion.
- L1-L3 can stay closer to the original behavior so the bot still trades actively.
- L4-L6 should require at least a meaningful SMC zone/trigger, not distance only.
- L7+ should require stronger confirmation: structure shift plus liquidity sweep plus OB/FVG zone before adding.
- Preferred risk control is `stop adding / wait for better recovery setup`, not `close basket at loss`.

Latest PSS V6 direction:

- Do not rework the user's original L1 entry behavior without explicit permission.
- Keep profit-close reliability as the main bugfix area.
- For DD reduction, focus on staged smart recovery entries from L4+, dynamic grid, lot curve, and close-profit execution.
