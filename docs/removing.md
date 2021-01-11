## Removing variants for one or more samples

To remove all variants from one or more samples of a dataset you can use the following command:

```
beacon delete variants

-ds TEXT      dataset ID  [required]
-sample TEXT  one or more samples to remove variants for  [required]

```
Note that dataset ID (-ds) and sample are mandatory parameters. To specify multiple samples you should use the `-sample` option multiple times.


## Removing a specific dataset

Use the command to remove a dataset from the database:
```
beacon delete dataset -id <dataset_id>

```
