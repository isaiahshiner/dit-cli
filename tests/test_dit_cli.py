"""Pytest unit tests"""


import os
import pytest

from dit_cli.cli import validate_dit
VALID_STR = 'dit is valid, no errors found'


@pytest.mark.short
@pytest.mark.parametrize("file_name,expected", [
    ('dits/conflicts1.dit', VALID_STR),
    ('dits/conflicts2.dit', VALID_STR),
    ('dits/empty.dit', 'file is empty'),
    ('dits/escape1.dit', VALID_STR),
    ('dits/eval1.dit', VALID_STR),
    ('dits/inheritance1.dit', VALID_STR),
    ('dits/list1.dit', VALID_STR),
    ('dits/list2.dit', VALID_STR),
    ('dits/misc1.dit', VALID_STR),
    ('dits/no-objects.dit', 'dit is valid, no objects to check'),
    ('dits/query1.dit', VALID_STR),
    ('dits/space3.dit', VALID_STR),
])
def test_validate(file_name, expected):
    result = validate_dit(get_file(file_name))
    assert result == expected


@pytest.mark.short
@pytest.mark.parametrize("file_name,expected", [
    ('fail/assigner1.dit', 'AssignError: Assigner "a" expected 1 args, got 2'),
    ('fail/assigner2.dit', 'AssignError: Undefined arg "garbage" for Assigner a'),
    ('fail/evaler1.dit', 'ValidationError<a>: This is a test error'),
    ('fail/evaler2.dit', '''CodeError: A Javascript Validator
Error message follows:

/tmp/dit/A-Validator.js:3
        const a = 2;
              ^

SyntaxError: Identifier 'a' has already been declared
    at Object.<anonymous> (/tmp/dit/A-Validator.js:5:23)
    at Module._compile (internal/modules/cjs/loader.js:778:30)
    at Object.Module._extensions..js (internal/modules/cjs/loader.js:789:10)
    at Module.load (internal/modules/cjs/loader.js:653:32)
    at tryModuleLoad (internal/modules/cjs/loader.js:593:12)
    at Function.Module._load (internal/modules/cjs/loader.js:585:3)
    at Function.Module.runMain (internal/modules/cjs/loader.js:831:12)
    at startup (internal/bootstrap/node.js:283:19)
    at bootstrapNodeJSCore (internal/bootstrap/node.js:623:3)
'''),
    ('fail/namespace-att1.dit', 'VarError: Expected string "A.value", got "B"'),
    ('fail/namespace-att2.dit', 'VarError: Expected class "A", got string'),
    ('fail/namespace-att3.dit', 'VarError: Expected "A", got "C"'),
    ('fail/namespace-att4.dit', 'VarError: "A.value" expected a list'),
    ('fail/namespace-att5.dit', 'VarError: Expected string "A.value", got list'),
    ('fail/namespace-att6.dit', 'VarError: Expected class "A", got list'),
    ('fail/namespace-def1.dit', 'VarError: "A" is already defined (class)'),
    ('fail/namespace-def2.dit', 'VarError: "A" is already defined (object)'),
    ('fail/namespace-def3.dit', 'VarError: "A" is already defined (namespace)'),
    ('fail/namespace-def4.dit', 'VarError: "A" is already defined (assigner)'),
    ('fail/namespace-obj1.dit', 'VarError: Expected class "A", got string'),
    ('fail/namespace-obj2.dit', 'VarError: Expected class "A", got list'),
    ('fail/namespace-obj3.dit', 'VarError: Expected "A", got "B"'),
    ('fail/namespace-var1.dit', 'VarError: Undefined variable "does" in "does.not.exist"'),
])
def test_raise(file_name, expected):
    result = validate_dit(get_file(file_name)).args[0]
    assert result == expected


@pytest.mark.long
@pytest.mark.parametrize("file_name,query,expected,", [
    ('dits/escape1.dit', 'print(e.escape1)', '''"Let's"'''),
    ('dits/query1.dit', 'print(name)', '"Jane Emily Marie Doe"'),
    ('dits/query1.dit', 'name',
     '''{"class":"FullName","print":"Jane Emily Marie Doe","givenName":{"class":"Name","print":"Jane","value":"Jane"},"middleNames":[{"class":"Name","print":"Emily","value":"Emily"},{"class":"Name","print":"Marie","value":"Marie"}],"familyName":{"class":"Name","print":"Doe","value":"Doe"}}'''),
])
def test_query(file_name, query, expected):
    result = validate_dit(get_file(file_name), query_string=query)
    assert result == expected


@pytest.mark.long
@pytest.mark.parametrize("file_name,expected", [
    ('../examples/fruit.dit', VALID_STR),
    ('../examples/import.dit', VALID_STR),
    ('../examples/length.dit', VALID_STR),
    ('../examples/name.dit', VALID_STR),
])
def test_examples(file_name, expected):
    result = validate_dit(get_file(file_name))
    assert result == expected


def get_file(file_name):
    """Helper to turn a test file name into the file"""
    with open(os.path.join(os.path.dirname(__file__), file_name)) as file_object:
        return file_object.read()
