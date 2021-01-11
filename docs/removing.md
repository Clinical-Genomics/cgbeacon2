## Removing variants for one or more samples using the command line

To remove all variants from one or more samples of a dataset you can use the following command:

```
beacon delete variants

-ds TEXT      dataset ID  [required]
-sample TEXT  one or more samples to remove variants for  [required]

```
Note that dataset ID (-ds) and sample are mandatory parameters. To specify multiple samples you should use the `-sample` option multiple times.


## Removing variants for one or more samples by using the API

Authorized users can also remove variants by sending a request to the /apiv1.0/delete endpoint. This endpoint accepts json data POST requests. If the request parameters are correct it will return a response with code 200 (success) and message "Deleting variants from Beacon", whole it will start the actual thread that will remove variants from the database.

The request to the add API should contain the following header parameters:
- **Content-Type**: application/json
- **X-Auth-Token**: auth_token

Auth-token is the token created in the moment an API user is created in the database (documentation [here](.loading.md)).

Example of a POST request to delete variants:
```
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Auth-Token: auth_token' \
  -d '{"dataset_id": "test_public",
  "samples" : ["ADM1059A1", "ADM1059A2"]}' http://localhost:5000/apiv1.0/delete
```

## Removing a specific dataset

Use the command to remove a dataset from the database:
```
beacon delete dataset -id <dataset_id>

```
