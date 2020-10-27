####### WRONG REQUEST PARAMS #######
NO_MANDATORY_PARAMS = dict(
    errorCode=400,
    errorMessage="Missing one or more mandatory parameters (referenceName, referenceBases, assemblyId)",
)

NO_SECONDARY_PARAMS = dict(
    errorCode=400, errorMessage="Either 'alternateBases' or 'variantType' param is required",
)

NO_POSITION_PARAMS = dict(
    errorCode=400, errorMessage="Start coordinate or range coordinate params are required",
)

INVALID_COORDINATES = dict(
    errorCode=400,
    errorMessage="invalid coordinates. Variant start and stop positions must be numbers",
)

BUILD_MISMATCH = dict(
    errorCode=400,
    errorMessage="Requested genome assembly is in conflict with the assembly of one or more requested datasets",
)
