# data360UpdateChecks

Generates shortlist of data updating results and verbose profiles of TC/Govdata360 datasets

Requires 1 input CSV file: "Answer Key" which contains the ideal start and end year dates for each dataset.
Note that this code assumes that this CSV has the following columns:
    ```['slug', 'title', 'source_name', 'source_link', 'legal_text',
       'legal_link', 'id', 'Dataset / sub-dataset', 'Site', 'Data Coverage',
       'Start Year', 'Latest Year']```

Generates 2 CSV files:
- 2017-07-29-Check-TC-Data-Update.csv == shortlist of datasets for updating and recommended action for each one
- 2017-07-29-Check-TC-Data-Update-verboseprofile.csv == complete profile of TC/Govdata360 datasets, including the ff. features:
  - number of unique countries
  - number of unique indicators
  - number of unique subindicators
  - current start year, excluding 100% NULL columns
  - end start year, excluding 100% NULL columns
  - whole timeframe (as a list), excluding 100% NULL columns
