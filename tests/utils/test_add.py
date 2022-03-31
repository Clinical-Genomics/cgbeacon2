import pytest
from cgbeacon2.utils.add import add_dataset
from pymongo.errors import DuplicateKeyError


def test_add_dataset_twice(public_dataset, database):
    """Test that the add_dataset function exits when the same dataset is added twice"""

    # WHEN a dataset is first saved to database
    result = add_dataset(database, public_dataset)

    # The function should return a non-None document ID
    assert result is not None

    # WHEN cli is invoked to add the same dataset again
    # THEN it should raise a pymongo DuplicateKeyError
    with pytest.raises(DuplicateKeyError) as error:
        add_dataset(database, public_dataset)
