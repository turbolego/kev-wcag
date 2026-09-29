# Evaluation Results: Kev-WCAG vs Kev Base

## Test Setup
- **Dataset**: hummern/wcag-kev-training (200 WCAG 2.2 patterns)
- **Evaluation date**: 2026-09-29
- **Test types**: Violation detection, criterion identification, severity estimation
- **Note**: Actual model training pending - results below are placeholders showing evaluation methodology

## Model Comparison

| Model | Violation Detection (Acc) | Criterion Identification (Acc) | Severity Estimation (Acc±1) |
|-------|---------------------------|--------------------------------|-----------------------------|
| Kev base (jaredpalmer/kev-4b) | TBD | TBD | TBD |
| Kev-WCAG (this repo) | TBD | TBD | TBD |

## Sample Predictions

### Expected behavior after training:

**Pattern: Low contrast text (light gray on white)**
```html
<p style="color: #ddd; background: white;">Hard to read text</p>
```

**Expected outputs:**
- Violation detection: YES (label: true)
- Criterion: 1.4.3 Contrast - Insufficient color contrast  
- Severity: 3 (Significant issue)
- Accessible check: NO (label: false)

**Pattern: Properly labeled input**
```html
<label for="email">Email</label>
<input type="email" id="email" name="email">
```

**Expected outputs:**
- Violation detection: NO (label: false)
- Criterion: No WCAG violation
- Severity: 0 (No issue)
- Accessible check: YES (label: true)

## Evaluation Script

See `evaluation/evaluate.py` for the full test suite.

## Per-Criteria Breakdown (Planned)

Once models are trained, evaluation will include:

### By WCAG Category
- Text alternatives (1.1)
- Time-based media (1.2) 
- Adaptable (1.3)
- Distinguishable (1.4)
- Keyboard operable (2.1)
- Enough time (2.2)
- Seizures and physical reactions (2.3)
- Navigable (2.4)
- Input modalities (2.5)
- Readable (3.1)
- Predictable (3.2)
- Input assistance (3.3)
- Compatible (4.1)

### By Severity Level
- Critical (4): Blocks access entirely
- Significant (3): Affects many users
- Moderate (2): Affects some users
- Minor (1): Low impact
- None (0): No issue

## Baseline Performance

The base Kev model (without WCAG fine-tuning) is expected to perform near random on these tasks since:
1. It was not trained on accessibility evaluation data
2. The WCAG-specific vocabulary and patterns are outside its training distribution
3. The model architecture is capable but needs task-specific fine-tuning

## Next Steps

1. Complete model training using the provided scripts
2. Run evaluation on both base and fine-tuned models
3. Update this file with actual results
4. Add confusion matrices and detailed error analysis

## References

- Evaluation methodology follows standard NLP fine-tuning evaluation practices
- WCAG 2.2 success criteria from https://www.w3.org/TR/WCAG22/
- Kev evaluation framework from https://github.com/jaredpalmer/kev