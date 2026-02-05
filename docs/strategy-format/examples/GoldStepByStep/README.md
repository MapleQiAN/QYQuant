# 黄金策略 Step-By-Step

This example packages the Gold Step-By-Step strategy as a QYSP bundle.

Strategy rules:
- Buy when price breaks the previous cycle peak.
- Sell if price drops more than 3% in a single day.
- Sell if price drops more than 6% from the cycle peak.

Run locally:
- `python src/strategy.py`
- Or import and call `main()` from `src/strategy.py`.
