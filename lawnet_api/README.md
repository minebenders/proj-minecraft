# lawnet-api
## Basic usage
`dotenv` is used to obtain the API keys required to call the Lawnet API. This is done for security.
Ensure that `.env` exists in the directory with the following variables set:
```
LN_CLIENT_ID=''
LN_CLIENT_SECRET=''
LN_X_API_KEY=''
LN_SEARCH_API_KEY=''
```
Search by calling `search()` from class `Post` in `search.py`.

```
search(searchTerm:str, cats:list, l2cats:list, l3cats:list,
           page:int=1, maxperpage:int=20, surroundingWords:int=10,
           orderBy:str='relevance')
```

Result of the search is provided as an `XMLResult` object. Read `.data` to obtain a list of dictionaries,
each containing 1 result.

Further documentation will be provided soon.
