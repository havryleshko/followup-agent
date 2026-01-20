# Follow-up Recommendations

## Summary

| Invoice ID | Client | Amount | Days Overdue | Timing | Tone | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| VIP-001 | Northwind Partners | 15000 USD | 12 | now | soft | yes |
| NEW-101 | Fresh Start LLC | 800 USD | 5 | wait_3_days | soft | yes |
| REC-550 | Global Manufacturing | 50000 USD | 8 | now | neutral | yes |
| RISK-777 | HighRisk Supply | 1200 USD | 65 | now | firm | yes |
| REC-221 | Evergreen Retail | 3200 USD | 20 | now | neutral | yes |
| VIP-204 | Summit Advisors | 2500 USD | 35 | now | soft | yes |

## Invoice 1: VIP-001

**Identifiers**
- Client: Northwind Partners
- Invoice ID: VIP-001
- Amount: 15000 USD
- Issue Date: 2024-12-01
- Days Overdue: 12

**Decision**
- Follow-up Required: True
- Timing: now
- Suggested Send Date: now
- Tone: soft

**Message Draft**
- Message: unavailable (not generated)

**Explanation**
inputs: days_overdue=12, amount=15000.0, relationship=vip, last_followup_days=none, risk=medium | rules: STANDARD_OVERDUE,RELATIONSHIP_SOFTEN | decision: followup_required=True, timing=now, tone=soft

## Invoice 2: NEW-101

**Identifiers**
- Client: Fresh Start LLC
- Invoice ID: NEW-101
- Amount: 800 USD
- Issue Date: 2025-01-05
- Days Overdue: 5

**Decision**
- Follow-up Required: True
- Timing: wait_3_days
- Suggested Send Date: in 3 days
- Tone: soft

**Message Draft**
- Message: unavailable (not generated)

**Explanation**
inputs: days_overdue=5, amount=800.0, relationship=new, last_followup_days=none, risk=low | rules: LOW_OVERDUE_WAIT,RELATIONSHIP_SOFTEN | decision: followup_required=True, timing=wait_3_days, tone=soft

## Invoice 3: REC-550

**Identifiers**
- Client: Global Manufacturing
- Invoice ID: REC-550
- Amount: 50000 USD
- Issue Date: 2024-11-15
- Days Overdue: 8

**Decision**
- Follow-up Required: True
- Timing: now
- Suggested Send Date: now
- Tone: neutral

**Message Draft**
- Message: unavailable (not generated)

**Explanation**
inputs: days_overdue=8, amount=50000.0, relationship=recurring, last_followup_days=380, risk=medium | rules: STANDARD_OVERDUE | decision: followup_required=True, timing=now, tone=neutral

## Invoice 4: RISK-777

**Identifiers**
- Client: HighRisk Supply
- Invoice ID: RISK-777
- Amount: 1200 USD
- Issue Date: 2024-10-01
- Days Overdue: 65

**Decision**
- Follow-up Required: True
- Timing: now
- Suggested Send Date: now
- Tone: firm

**Message Draft**
- Message: unavailable (not generated)

**Explanation**
inputs: days_overdue=65, amount=1200.0, relationship=risky, last_followup_days=415, risk=high | rules: URGENT_OVERDUE,RELATIONSHIP_FIRM | decision: followup_required=True, timing=now, tone=firm

## Invoice 5: REC-221

**Identifiers**
- Client: Evergreen Retail
- Invoice ID: REC-221
- Amount: 3200 USD
- Issue Date: 2024-12-20
- Days Overdue: 20

**Decision**
- Follow-up Required: True
- Timing: now
- Suggested Send Date: now
- Tone: neutral

**Message Draft**
- Message: unavailable (not generated)

**Explanation**
inputs: days_overdue=20, amount=3200.0, relationship=recurring, last_followup_days=none, risk=medium | rules: STANDARD_OVERDUE | decision: followup_required=True, timing=now, tone=neutral

## Invoice 6: VIP-204

**Identifiers**
- Client: Summit Advisors
- Invoice ID: VIP-204
- Amount: 2500 USD
- Issue Date: 2024-12-28
- Days Overdue: 35

**Decision**
- Follow-up Required: True
- Timing: now
- Suggested Send Date: now
- Tone: soft

**Message Draft**
- Message: unavailable (not generated)

**Explanation**
inputs: days_overdue=35, amount=2500.0, relationship=vip, last_followup_days=383, risk=medium | rules: URGENT_OVERDUE,RELATIONSHIP_SOFTEN,SOFTEN_NOTES | decision: followup_required=True, timing=now, tone=soft
