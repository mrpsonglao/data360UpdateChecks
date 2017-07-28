# importing required modules
import pandas as pd
import numpy as np
import requests
import datetime
import re
import io

def clean_up_dates(x):
    cleaned_date = x
    m = re.match('(\d{4})-(\d{4})', str(x))
    if m:
        cleaned_date = m.groups()[-1]
    else:
        n = re.match('(\d{4})Q\d{1}', str(x))
        if n:
            cleaned_date = n.groups()[-1]
        else:
            o = re.match('(\d{4})M\d{2}', str(x))
            if o:
                cleaned_date = o.groups()[-1]
    return cleaned_date

def amida_action(x):
    action = "Updated. No action required."

    end = x['end_year-check']
    start = x['start_year-check']

    if (not end) & (not start):
        action = "Not updated (both start and end dates)"
    elif end & (not start):
        action = "Not updated (start date only)"
    elif (not end) & (start):
        action = "Not updated (end date only)"

    if (x['Site'] == 'gv') & (action != "Updated. No action required."):
        action = "[Gov dataset - For Luis' action] " + action

    return action

def main():


    date_today = datetime.date.today().isoformat()

    # getting user input for data files
    ans_key = input("""What's the filename of the CSV file which contains the ideal start and end year dates for each dataset?

                     Note that this code assumes that this CSV has the following columns:
                     ['slug', 'title', 'source_name', 'source_link', 'legal_text',
       'legal_link', 'id', 'Dataset / sub-dataset', 'Site', 'Data Coverage',
       'Start Year', 'Latest Year']""")

    # Load Data
    df_answer_key = pd.read_csv(ans_key + '.csv', encoding='latin-1')

    # load all TC/Gov360 datasets
    tc_datasets = 'http://tcdata360-backend.worldbank.org/api/v1/datasets'
    df_tc_datasets = pd.read_json(requests.get(tc_datasets).text)

    # compiling features per TCdata360 dataset
    data_columns = ['title', 'id', 'number_of_unique_countries', 'number_of_unique_indicators',
                    'number_of_unique_subindicators',
                    'start_year', 'end_year', 'timeframe']
    tc_data_check = pd.DataFrame()

    success_counter = 0
    error_counter = 0
    error_list = []
    total_count = len(df_tc_datasets.index)

    for row in df_tc_datasets.index:
        id_dataset = df_tc_datasets['id'].ix[row]
        title_dataset = df_tc_datasets['title'].ix[row]

        dat_url = "http://tcdata360-backend.worldbank.org/api/v1/datasets/" + str(id_dataset) + "/dump.csv"
        dat = requests.get(dat_url)
        df_dat = pd.read_csv(io.StringIO(dat.text))

        # drop all completele NULL columns and rows
        df_dat.dropna(axis=1, how='all', inplace=True)
        df_dat.dropna(axis=0, how='all', inplace=True)

        try:
            # Generate features for checking
            num_of_countries = len(df_dat['Country ISO3'].value_counts().index)
            num_of_indicators = len(df_dat['Indicator'].value_counts().index)
            num_of_subindicators = df_dat[['Indicator', 'Subindicator Type']].drop_duplicates().shape[0]

            nondate_cols = ['Country ISO3', 'Country Name', 'Indicator', 'Subindicator Type', 'Partner', 'MRV',
                            'Product']
            list_timeframe = [col for col in df_dat.columns if col not in nondate_cols]
            list_timeframe = sorted(list_timeframe)
            start_year = list_timeframe[0]
            end_year = list_timeframe[-1]

            # compile all data
            dataset_list = [title_dataset, id_dataset, num_of_countries, num_of_indicators, num_of_subindicators,
                            start_year, end_year, list_timeframe]

            df_temp = pd.DataFrame(dataset_list).T
            tc_data_check = tc_data_check.append(pd.DataFrame(dataset_list).T)

        except:
            error_counter += 1
            error_list.append([title_dataset, id_dataset])
            print("Failed loading %s with dataset ID %s." % (title_dataset, str(id_dataset)))
            continue

        success_counter += 1

        print("Done checking %d out of %d datasets." % (success_counter + error_counter, total_count))

    # Clean up final dataframe
    tc_data_check.columns = data_columns
    tc_data_check.reset_index(drop=True, inplace=True)

    print("Done with all %d datasets with %d successes and %d failures." % (total_count, success_counter, error_counter))
    print("Failed datasets include %s" % str(error_list))

    # Merge against TC dataset file
    df_tc_data_check = df_tc_datasets[['slug', 'id', 'source', 'title']].merge(tc_data_check, how="outer",
                                                                               on=['id', 'title'])

    df_tc_data_check['start_year-clean'] = df_tc_data_check['start_year'].apply(lambda x: clean_up_dates(x))
    df_tc_data_check['end_year-clean'] = df_tc_data_check['end_year'].apply(lambda x: clean_up_dates(x))

    # ensure IDs are type String
    df_tc_data_check['id'] = df_tc_data_check['id'].astype(str)
    df_answer_key['id'] = df_answer_key['id'].astype(str)

    df_merge = df_tc_data_check.merge(df_answer_key, how='outer', on=['id', 'slug', 'title'])
    df_merge_shortlist = df_merge[
        ['id', 'title', 'slug', 'Site', 'start_year-clean', 'end_year-clean', 'Start Year', 'Latest Year']].dropna(
        axis=0, how='any', subset=['id', 'start_year-clean', 'Start Year'])

    df_merge_shortlist = df_merge_shortlist[(df_merge_shortlist['Start Year'] != 'N/A (duplicate dataset)') & (
    df_merge_shortlist['Start Year'] != 'N/A (too general)')]

    df_merge_shortlist['start_year-check'] = df_merge_shortlist['start_year-clean'] <= df_merge_shortlist['Start Year']
    df_merge_shortlist['end_year-check'] = df_merge_shortlist['end_year-clean'] >= df_merge_shortlist['Latest Year']

    df_merge_shortlist['amida_action'] = df_merge_shortlist.apply(lambda x: amida_action(x), axis=1)

    df_merge_shortlist.columns = ['id', 'title', 'slug', 'Site', 'current-start_year', 'current-end_year',
                                  'ideal-start_year', 'ideal-end_year', 'start_year-check', 'end_year-check',
                                  'amida_action']

    df_merge_shortlist.to_csv("%s-Check-TC-Data-Update.csv" % date_today, index=False)
    df_merge.to_csv("%s-Check-TC-Data-Update-verboseprofile.csv" % date_today, index=False)

if __name__ == '__main__':
    main()