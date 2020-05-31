import unittest
import numpy as np
import pandas as pd

from pathlib import Path
from pandas.testing import assert_frame_equal


class TestOutput(unittest.TestCase):

    @classmethod
    def setUp(self):
        '''
        Set up the self.output_df dataframe from the .json output file.
        '''
        self.output_df = pd.read_json('output.json')

        court_map = {
            'High Court': 'SGHC',
            'Court of Appeal': 'SGCA',
            'District Court': 'SGDC',
            'Court of Criminal Appeal': 'SGCA'
        }

        self.output_df['Court'] = self.output_df.Court.map(court_map)
        ref_columns = {
            0: 'refSLR',
            1: 'ref'
        }

        # Split reference into SLR reference and normal reference
        self.output_df[list(ref_columns.values())] = pd.DataFrame(
            self.output_df.reference.apply(pd.Series)).rename(columns=ref_columns)
        ref_na = self.output_df['ref'].isna()
        self.output_df.loc[ref_na, 'ref'], self.output_df.loc[ref_na,
                                                              'refSLR'] = self.output_df.refSLR[ref_na], np.nan
        self.output_df.drop('reference', axis=1, inplace=True)

        # Construct the unique reference
        self.exploded_output = self.output_df.explode('parties')
        self.output_df = self.exploded_output.loc[self.exploded_output.parties.str.lower(
        ) != "public prosecutor"].copy()
        self.output_df['unique_ref'] = self.output_df['ref'] + \
            ' ' + self.output_df['parties']
        self.output_df.unique_ref = self.output_df.unique_ref.str.upper().str.replace(
            "AND ANOTHER", "").str.replace("AND OTHERS", "").str.replace(' +', ' ').str.strip()
        self.output_df = self.output_df[['unique_ref', 'Date', 'Court',
                                         'coram', 'counsel', 'parties', 'paragraphs']]
        self.output_df.rename(columns={'parties': 'accused'}, inplace=True)

        '''
        Set up the self.true_df dataframe from the .tsv file.
        '''

        tsv_path = Path('MDA Spreadsheets')
        self.true_df = pd.read_csv(
            tsv_path/'6.0 MDA Spreadsheet - Merged Trials & AAC.tsv', sep='\t', header=[1], index_col=0)

        # Construct unique reference, rename unnamed column, drop repeated columns, shift unique_ref to front
        self.true_df.reset_index(drop=True, inplace=True)
        self.true_df['unique_ref'] = (self.true_df.Reference + ' ' +
                                      self.true_df['Accused Person']).str.strip()
        self.true_df.unique_ref = self.true_df.unique_ref.str.upper()
        self.true_df.rename(columns={"Unnamed: 63": "Remarks"}, inplace=True)
        self.true_df.drop(
            ['Year', 'Reference', 'Accused Person'], axis=1, inplace=True)
        cols = list(self.true_df)
        cols.insert(0, cols.pop(cols.index('unique_ref')))
        self.true_df = self.true_df.loc[:, cols]

        '''
        Set up the respective aligned dataframes for comparison.
        Aligned dataframes are the subset of the base dataframe that only contains the information
            that are common in both, and exclude the set of information that is contained in one
            dataframe but not the other.
        '''
        aligned = list(set(self.output_df.unique_ref).intersection(
            set(self.true_df.unique_ref)))

        self.output_df_aligned = self.output_df.loc[self.output_df.unique_ref.isin(
            aligned)].sort_values('unique_ref').copy()

        self.true_df_aligned = self.true_df.loc[self.true_df.unique_ref.isin(
            aligned)].sort_values('unique_ref').copy()

    def test_all_cases_have_pp(self):
        '''
        Verifies that all cases have PP in 'parties'.
        This is accomplished by checking how many exploded PP rows there are and
            comparing that to the length of the original dataframe.
        '''
        self.assertTrue(len(self.exploded_output.loc[self.exploded_output.parties.str.lower(
        ) != "public prosecutor"]) == len(self.output_df))

    def test_output_df_unique_ref_is_unique(self):
        '''
        For self.output_df, verifies that the unique reference for every line only occurs once in the column.
        '''
        self.assertTrue(self.output_df.unique_ref.value_counts()[0] == 1)

    def test_true_df_unique_ref_is_unique(self):
        '''
        For self.true_df, verifies that the unique reference for every line only occurs once in the column.
        '''
        self.assertTrue(self.true_df.unique_ref.value_counts()[0] == 1)

    def test_dfs_are_aligned(self):
        '''
        Verifies that self.output_df and self.true_df have the same cases.
        '''
        self.assertTrue(len(set(self.output_df.unique_ref) -
                            set(self.true_df.unique_ref)) == 0)

        self.assertTrue(len(set(self.true_df.unique_ref) -
                            set(self.output_df.unique_ref)) == 0)

    def _test_aligned(self, output_df_field: str, input_df_field: str):
        '''
        Reusable wrapper for testing fields - not a test in and of itself.
        Verifies that the fields are the same across both dataframes.
        '''
        assert_frame_equal(self.output_df_aligned[['unique_ref', output_df_field]],
                           self.true_df_aligned[[
                               'unique_ref', input_df_field]],
                           check_index_type=False,
                           check_names=False)

    def test_aligned_date(self):
        '''
        Verifies that the date is the same across both dataframes.
        '''
        self._test_aligned(output_df_field='Date', input_df_field='Date')

    def test_aligned_court(self):
        '''
        Verifies that the court is the same across both dataframes.
        '''
        self._test_aligned(output_df_field='Court', input_df_field='Court')


if __name__ == '__main__':
    unittest.main()
