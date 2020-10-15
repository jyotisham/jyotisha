## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 16s
```
  update_festival_details: 4172.53ms for      2 calls
            compute_angas: 7089.84ms for      1 calls
  get_all_angas_in_period:    3.01ms for   1910 calls
assign_festivals_from_rules: 1702.94ms for      2 calls
          assign_festival:    0.01ms for  481070 calls
assign_tithi_yoga_nakshatra_fest:    0.05ms for  43848 calls
           set_rule_dicts:  568.07ms for      1 calls
             dump_to_file:  476.36ms for      1 calls
                     find:    3.19ms for    107 calls
  assign_festival_numbers:    2.03ms for      2 calls
```

## Comment:
