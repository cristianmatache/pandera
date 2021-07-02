"""Unit tests for io module"""

import platform
import tempfile
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest
from packaging import version

import pandera as pa
import pandera.extensions as pa_ext
import pandera.typing as pat

try:
    from pandera import io
except ImportError:
    HAS_IO = False
else:
    HAS_IO = True


try:
    import yaml
except ImportError:  # pragma: no cover
    PYYAML_VERSION = None
else:
    PYYAML_VERSION = version.parse(yaml.__version__)  # type: ignore


SKIP_YAML_TESTS = PYYAML_VERSION is None or PYYAML_VERSION.release < (5, 1, 0)  # type: ignore


# skip all tests in module if "io" depends aren't installed
pytestmark = pytest.mark.skipif(
    not HAS_IO, reason='needs "io" module dependencies'
)


def _create_schema(index="single"):

    if index == "multi":
        index = pa.MultiIndex(
            [
                pa.Index(pa.Int, name="int_index0"),
                pa.Index(pa.Int, name="int_index1"),
                pa.Index(pa.Int, name="int_index2"),
            ]
        )
    elif index == "single":
        # make sure io modules can handle case when index name is None
        index = pa.Index(pa.Int, name=None)
    else:
        index = None

    return pa.DataFrameSchema(
        columns={
            "int_column": pa.Column(
                pa.Int,
                checks=[
                    pa.Check.greater_than(0),
                    pa.Check.less_than(10),
                    pa.Check.in_range(0, 10),
                ],
            ),
            "float_column": pa.Column(
                pa.Float,
                checks=[
                    pa.Check.greater_than(-10),
                    pa.Check.less_than(20),
                    pa.Check.in_range(-10, 20),
                ],
            ),
            "str_column": pa.Column(
                pa.String,
                checks=[
                    pa.Check.isin(["foo", "bar", "x", "xy"]),
                    pa.Check.str_length(1, 3),
                ],
            ),
            "datetime_column": pa.Column(
                pa.DateTime,
                checks=[
                    pa.Check.greater_than(pd.Timestamp("20100101")),
                    pa.Check.less_than(pd.Timestamp("20200101")),
                ],
            ),
            "timedelta_column": pa.Column(
                pa.Timedelta,
                checks=[
                    pa.Check.greater_than(pd.Timedelta(1000, unit="ns")),
                    pa.Check.less_than(pd.Timedelta(10000, unit="ns")),
                ],
            ),
            "optional_props_column": pa.Column(
                pa.String,
                nullable=True,
                allow_duplicates=True,
                coerce=True,
                required=False,
                regex=True,
                checks=[pa.Check.str_length(1, 3)],
            ),
            "notype_column": pa.Column(
                checks=pa.Check.isin(["foo", "bar", "x", "xy"]),
            ),
        },
        index=index,
        coerce=False,
        strict=True,
    )


YAML_SCHEMA = f"""
schema_type: dataframe
version: {pa.__version__}
columns:
  int_column:
    pandas_dtype: int
    nullable: false
    checks:
      greater_than: 0
      less_than: 10
      in_range:
        min_value: 0
        max_value: 10
    allow_duplicates: true
    coerce: false
    required: true
    regex: false
  float_column:
    pandas_dtype: float
    nullable: false
    checks:
      greater_than: -10
      less_than: 20
      in_range:
        min_value: -10
        max_value: 20
    allow_duplicates: true
    coerce: false
    required: true
    regex: false
  str_column:
    pandas_dtype: str
    nullable: false
    checks:
      isin:
      - foo
      - bar
      - x
      - xy
      str_length:
        min_value: 1
        max_value: 3
    allow_duplicates: true
    coerce: false
    required: true
    regex: false
  datetime_column:
    pandas_dtype: datetime64[ns]
    nullable: false
    checks:
      greater_than: '2010-01-01 00:00:00'
      less_than: '2020-01-01 00:00:00'
    allow_duplicates: true
    coerce: false
    required: true
    regex: false
  timedelta_column:
    pandas_dtype: timedelta64[ns]
    nullable: false
    checks:
      greater_than: 1000
      less_than: 10000
    allow_duplicates: true
    coerce: false
    required: true
    regex: false
  optional_props_column:
    pandas_dtype: str
    nullable: true
    checks:
      str_length:
        min_value: 1
        max_value: 3
    allow_duplicates: true
    coerce: true
    required: false
    regex: true
  notype_column:
    pandas_dtype: null
    nullable: false
    checks:
      isin:
      - foo
      - bar
      - x
      - xy
    allow_duplicates: true
    coerce: false
    required: true
    regex: false
checks: null
index:
- pandas_dtype: int
  nullable: false
  checks: null
  name: null
  coerce: false
coerce: false
strict: true
"""


def _create_schema_null_index():

    return pa.DataFrameSchema(
        columns={
            "float_column": pa.Column(
                pa.Float,
                checks=[
                    pa.Check.greater_than(-10),
                    pa.Check.less_than(20),
                    pa.Check.in_range(-10, 20),
                ],
            ),
            "str_column": pa.Column(
                pa.String,
                checks=[
                    pa.Check.isin(["foo", "bar", "x", "xy"]),
                    pa.Check.str_length(1, 3),
                ],
            ),
        },
        index=None,
    )


YAML_SCHEMA_NULL_INDEX = f"""
schema_type: dataframe
version: {pa.__version__}
columns:
  float_column:
    pandas_dtype: float
    nullable: false
    checks:
      greater_than: -10
      less_than: 20
      in_range:
        min_value: -10
        max_value: 20
  str_column:
    pandas_dtype: str
    nullable: false
    checks:
      isin:
      - foo
      - bar
      - x
      - xy
      str_length:
        min_value: 1
        max_value: 3
index: null
checks: null
coerce: false
strict: false
"""


def _create_schema_python_types():
    return pa.DataFrameSchema(
        {
            "int_column": pa.Column(int),
            "float_column": pa.Column(float),
            "str_column": pa.Column(str),
            "object_column": pa.Column(object),
        }
    )


YAML_SCHEMA_PYTHON_TYPES = f"""
schema_type: dataframe
version: {pa.__version__}
columns:
  int_column:
    pandas_dtype: int64
  float_column:
    pandas_dtype: float64
  str_column:
    pandas_dtype: str
  object_column:
    pandas_dtype: object
checks: null
index: null
coerce: false
strict: false
"""


YAML_SCHEMA_MISSING_GLOBAL_CHECK = f"""
schema_type: dataframe
version: {pa.__version__}
columns:
  int_column:
    pandas_dtype: int64
  float_column:
    pandas_dtype: float64
  str_column:
    pandas_dtype: str
  object_column:
    pandas_dtype: object
checks:
  unregistered_check:
    stat1: missing_str_stat
    stat2: 11
index: null
coerce: false
strict: false
"""


YAML_SCHEMA_MISSING_COLUMN_CHECK = f"""
schema_type: dataframe
version: {pa.__version__}
columns:
  int_column:
    pandas_dtype: int64
    checks:
      unregistered_check:
        stat1: missing_str_stat
        stat2: 11
  float_column:
    pandas_dtype: float64
  str_column:
    pandas_dtype: str
  object_column:
    pandas_dtype: object
index: null
coerce: false
strict: false
"""


@pytest.mark.skipif(
    SKIP_YAML_TESTS,
    reason="pyyaml >= 5.1.0 required",
)
def test_inferred_schema_io():
    """Test that inferred schema can be written to yaml."""
    df = pd.DataFrame(
        {
            "column1": [5, 10, 20],
            "column2": [5.0, 1.0, 3.0],
            "column3": ["a", "b", "c"],
        }
    )
    schema = pa.infer_schema(df)
    schema_yaml_str = schema.to_yaml()
    schema_from_yaml = io.from_yaml(schema_yaml_str)
    assert schema == schema_from_yaml


@pytest.mark.skipif(
    SKIP_YAML_TESTS,
    reason="pyyaml >= 5.1.0 required",
)
def test_to_yaml():
    """Test that to_yaml writes to yaml string."""
    schema = _create_schema()
    yaml_str = io.to_yaml(schema)
    assert yaml_str.strip() == YAML_SCHEMA.strip()

    yaml_str_schema_method = schema.to_yaml()
    assert yaml_str_schema_method.strip() == YAML_SCHEMA.strip()


@pytest.mark.skipif(
    SKIP_YAML_TESTS,
    reason="pyyaml >= 5.1.0 required",
)
@pytest.mark.parametrize(
    "yaml_str, schema_creator",
    [
        [YAML_SCHEMA, _create_schema],
        [YAML_SCHEMA_NULL_INDEX, _create_schema_null_index],
        [YAML_SCHEMA_PYTHON_TYPES, _create_schema_python_types],
    ],
)
def test_from_yaml(yaml_str, schema_creator):
    """Test that from_yaml reads yaml string."""
    schema_from_yaml = io.from_yaml(yaml_str)
    expected_schema = schema_creator()
    assert schema_from_yaml == expected_schema
    assert expected_schema == schema_from_yaml


def test_from_yaml_unregistered_checks():
    """Test that from_yaml raises an exception when deserializing unregistered checks."""

    with pytest.raises(AttributeError, match=".*custom checks.*"):
        io.from_yaml(YAML_SCHEMA_MISSING_COLUMN_CHECK)

    with pytest.raises(AttributeError, match=".*custom checks.*"):
        io.from_yaml(YAML_SCHEMA_MISSING_GLOBAL_CHECK)


def test_from_yaml_load_required_fields():
    """Test that dataframe schemas do not require any field."""
    io.from_yaml("")

    with pytest.raises(
        pa.errors.SchemaDefinitionError, match=".*must be a mapping.*"
    ):
        io.from_yaml(
            """
        - value
        """
        )


def test_io_yaml_file_obj():
    """Test read and write operation on file object."""
    schema = _create_schema()

    # pass in a file object
    with tempfile.NamedTemporaryFile("w+") as f:
        output = schema.to_yaml(f)
        assert output is None
        f.seek(0)
        schema_from_yaml = pa.DataFrameSchema.from_yaml(f)
        assert schema_from_yaml == schema


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="skipping due to issues with opening file names for temp files.",
)
@pytest.mark.parametrize("index", ["single", "multi", None])
def test_io_yaml(index):
    """Test read and write operation on file names."""
    schema = _create_schema(index)

    # pass in a file name
    with tempfile.NamedTemporaryFile("w+") as f:
        output = io.to_yaml(schema, f.name)
        assert output is None
        schema_from_yaml = io.from_yaml(f.name)
        assert schema_from_yaml == schema

    # pass in a Path object
    with tempfile.NamedTemporaryFile("w+") as f:
        output = schema.to_yaml(Path(f.name))
        assert output is None
        schema_from_yaml = pa.DataFrameSchema.from_yaml(Path(f.name))
        assert schema_from_yaml == schema


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="skipping due to issues with opening file names for temp files.",
)
@pytest.mark.parametrize("index", ["single", "multi", None])
def test_to_script(index):
    """Test writing DataFrameSchema to a script."""
    schema_to_write = _create_schema(index)

    for script in [io.to_script(schema_to_write), schema_to_write.to_script()]:

        local_dict = {}
        # pylint: disable=exec-used
        exec(script, globals(), local_dict)

        schema = local_dict["schema"]

        # executing script should result in a variable `schema`
        assert schema == schema_to_write

    with tempfile.NamedTemporaryFile("w+") as f:
        schema_to_write.to_script(Path(f.name))
        # pylint: disable=exec-used
        exec(f.read(), globals(), local_dict)
        schema = local_dict["schema"]
        assert schema == schema_to_write


def test_to_script_lambda_check():
    """Test writing DataFrameSchema to a script with lambda check."""
    schema1 = pa.DataFrameSchema(
        {
            "a": pa.Column(
                pa.Int,
                checks=pa.Check(lambda s: s.mean() > 5, element_wise=False),
            ),
        }
    )

    with pytest.warns(UserWarning):
        pa.io.to_script(schema1)

    schema2 = pa.DataFrameSchema(
        {
            "a": pa.Column(
                pa.Int,
            ),
        },
        checks=pa.Check(lambda s: s.mean() > 5, element_wise=False),
    )

    with pytest.warns(UserWarning, match=".*registered checks.*"):
        pa.io.to_script(schema2)


def test_to_yaml_lambda_check():
    """Test writing DataFrameSchema to a yaml with lambda check."""
    schema = pa.DataFrameSchema(
        {
            "a": pa.Column(
                pa.Int,
                checks=pa.Check(lambda s: s.mean() > 5, element_wise=False),
            ),
        }
    )

    with pytest.warns(UserWarning):
        pa.io.to_yaml(schema)


def test_format_checks_warning():
    """Test that unregistered checks raise a warning when formatting checks."""
    with pytest.warns(UserWarning):
        io._format_checks({"my_check": None})


@mock.patch("pandera.Check.REGISTERED_CUSTOM_CHECKS", new_callable=dict)
def test_to_yaml_registered_dataframe_check(_):
    """
    Tests that writing DataFrameSchema with a registered dataframe check works.
    """
    ncols_gt_called = False

    @pa_ext.register_check_method(statistics=["column_count"])
    def ncols_gt(pandas_obj: pd.DataFrame, column_count: int) -> bool:
        """test registered dataframe check"""

        # pylint: disable=unused-variable
        nonlocal ncols_gt_called
        ncols_gt_called = True
        assert isinstance(column_count, int), "column_count must be integral"
        assert isinstance(
            pandas_obj, pd.DataFrame
        ), "ncols_gt should only be applied to DataFrame"
        return len(pandas_obj.columns) > column_count

    assert (
        len(pa.Check.REGISTERED_CUSTOM_CHECKS) == 1
    ), "custom check is registered"

    schema = pa.DataFrameSchema(
        {
            "a": pa.Column(
                pa.Int,
            ),
        },
        checks=[pa.Check.ncols_gt(column_count=5)],
    )

    serialized = pa.io.to_yaml(schema)
    loaded = pa.io.from_yaml(serialized)

    assert len(loaded.checks) == 1, "global check was stripped"

    with pytest.raises(pa.errors.SchemaError):
        schema.validate(pd.DataFrame(data={"a": [1]}))

    assert ncols_gt_called, "did not call ncols_gt"


def test_to_yaml_custom_dataframe_check():
    """Tests that writing DataFrameSchema with an unregistered check raises."""

    schema = pa.DataFrameSchema(
        {
            "a": pa.Column(
                pa.Int,
            ),
        },
        checks=[pa.Check(lambda obj: len(obj.index) > 1)],
    )

    with pytest.warns(UserWarning, match=".*registered checks.*"):
        pa.io.to_yaml(schema)

    # the unregistered column check case is tested in
    # `test_to_yaml_lambda_check`


def test_to_yaml_bugfix_419():
    """Ensure that GH#419 is fixed"""
    # pylint: disable=no-self-use

    class CheckedSchemaModel(pa.SchemaModel):
        """Schema with a global check"""

        a: pat.Series[pat.Int64]
        b: pat.Series[pat.Int64]

        @pa.dataframe_check()
        def unregistered_check(self, _):
            """sample unregistered check"""
            ...

    with pytest.warns(UserWarning, match=".*registered checks.*"):
        CheckedSchemaModel.to_yaml()
