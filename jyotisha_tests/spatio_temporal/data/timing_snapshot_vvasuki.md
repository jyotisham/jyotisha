## Command
From `pytest -k tests.spatio_temporal.test_annual.test_timing` on vvasuki's machine.

## Results
run time: 14.5s
```
            compute_angas: 7060.72ms for      1 calls
  update_festival_details: 3309.96ms for      2 calls
  get_all_angas_in_period:    3.01ms for   1910 calls
assign_festivals_from_rules:  990.96ms for      2 calls
          assign_festival:    0.00ms for  481070 calls
           set_rule_dicts:  793.11ms for      1 calls
assign_tithi_yoga_nakshatra_fest:    0.02ms for  43848 calls
             dump_to_file:  507.43ms for      1 calls
                     find:    3.12ms for    107 calls
  assign_festival_numbers:    2.09ms for      2 calls
```

## Comment:
