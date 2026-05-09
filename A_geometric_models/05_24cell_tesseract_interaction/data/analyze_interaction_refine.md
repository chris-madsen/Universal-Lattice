# 24-cell / Tesseract Interaction Refinement

- focus classes: `['T4_C4', 'T4_C5', 'T4_C6', 'T4_C7', 'T3_C4', 'T3_C5', 'T3_C6', 'T2_C8']`
- samples per class: `3000`
- best family5 class: `T3_C4`
- best exact-profile class: `T4_C6`

## Ranked Focus Classes
- `T3_C4` -> family5_hits=`99` (0.0330), exact_profile_hits=`0` (0.0000), best=`{'class': 'T3_C4', 'tesseract_count': 3, 'cell_count': 4, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 2, 2], 'profile_score': 1.333333333333333, 'exact_profile_hit': False}`
- `T3_C5` -> family5_hits=`30` (0.0100), exact_profile_hits=`0` (0.0000), best=`{'class': 'T3_C5', 'tesseract_count': 3, 'cell_count': 5, 'family_count': 5, 'family_multiplicities': [1, 1, 2, 2, 2], 'profile_score': 1.1111111111111112, 'exact_profile_hit': False}`
- `T4_C4` -> family5_hits=`30` (0.0100), exact_profile_hits=`0` (0.0000), best=`{'class': 'T4_C4', 'tesseract_count': 4, 'cell_count': 4, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 2, 3], 'profile_score': 1.925925925925926, 'exact_profile_hit': False}`
- `T3_C6` -> family5_hits=`7` (0.0023), exact_profile_hits=`0` (0.0000), best=`{'class': 'T3_C6', 'tesseract_count': 3, 'cell_count': 6, 'family_count': 5, 'family_multiplicities': [1, 1, 2, 2, 3], 'profile_score': 0.6666666666666667, 'exact_profile_hit': False}`
- `T4_C5` -> family5_hits=`4` (0.0013), exact_profile_hits=`0` (0.0000), best=`{'class': 'T4_C5', 'tesseract_count': 4, 'cell_count': 5, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 2, 4], 'profile_score': 2.666666666666667, 'exact_profile_hit': False}`
- `T4_C6` -> family5_hits=`3` (0.0010), exact_profile_hits=`2` (0.0007), best=`{'class': 'T4_C6', 'tesseract_count': 4, 'cell_count': 6, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 2, 5], 'profile_score': 4.074074074074074, 'exact_profile_hit': False}`
- `T2_C8` -> family5_hits=`2` (0.0007), exact_profile_hits=`2` (0.0007), best=`{'class': 'T2_C8', 'tesseract_count': 2, 'cell_count': 8, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 1, 6], 'profile_score': 6.074074074074074, 'exact_profile_hit': True}`
- `T4_C7` -> family5_hits=`0` (0.0000), exact_profile_hits=`0` (0.0000), best=`{'class': 'T4_C7', 'tesseract_count': 4, 'cell_count': 7, 'family_count': 6, 'family_multiplicities': [1, 1, 1, 1, 3, 4], 'profile_score': 108.0, 'exact_profile_hit': False}`

## Comparison To Branches 08 / 09
- branch 08 best class: `L5_S5`; family5=`0.0004`; exact=`0.0004`
- branch 09 best class: `A4_L6_H0`; family5=`0.0004`; exact=`0.0000`
- branch 05 best family5 class: `T3_C4`; family5=`0.0330`
- branch 05 best exact-profile class: `T4_C6`; exact=`0.0007`
