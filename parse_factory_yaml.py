import yaml
from numbers import Number
from functools import partial

from DataGenerator import SObjectFactory, FieldFactory, SimpleValue, ChildRecordValue
from cumulusci.core.template_utils import format_str
from template_funcs import template_funcs


def parse_field_value(field):
    assert field is not None
    if isinstance(field, str) or isinstance(field, Number):
        return SimpleValue(field)
    elif isinstance(field, dict):
        return ChildRecordValue(parse_sobject_definition(field))
    else:
        assert False, "Unknown field type"


def parse_field(name, definition):
    assert name, name
    assert definition is not None, f"Field should have a definition: {name}"
    return FieldFactory(name, parse_field_value(definition))


def parse_fields(fields):
    return [parse_field(name, definition) for name, definition in fields.items()]


def parse_friends(friends):
    return parse_sobject_list(friends)


def evaluate(value):
    funcs = {name: partial(func, None) for name, func in template_funcs.items()}

    if isinstance(value, str) and "{" in value:
        return format_str(value, **funcs)
    else:
        return value


def parse_count_expression(yaml_sobj, sobj_def):
    numeric_expr = yaml_sobj["count"]
    if isinstance(numeric_expr, Number):
        sobj_def["count"] = int(numeric_expr)
    elif isinstance(numeric_expr, str):
        if "<<" in numeric_expr or "=" in numeric_expr:
            sobj_def["count_expr"] = SimpleValue(numeric_expr)
            sobj_def["count"] = None
        else:
            sobj_def["count"] = int(numeric_expr)
    else:
        raise ValueError(
            f"Expected count of {yaml_sobj['type']} to be a number, not {numeric_expr}"
        )


def parse_sobject_definition(yaml_sobj):
    assert yaml_sobj
    sobj_def = {}
    sobj_def["sftype"] = yaml_sobj["type"]
    sobj_def["fields"] = parse_fields(yaml_sobj.get("fields", {}))
    sobj_def["friends"] = parse_friends(yaml_sobj.get("friends", []))
    sobj_def["nickname"] = yaml_sobj.get("nickname")
    count_expr = yaml_sobj.get("count")
    if count_expr is not None:
        parse_count_expression(yaml_sobj, sobj_def)

    return SObjectFactory(**sobj_def)


def parse_sobject_list(sobjects):
    parsed_sobject_definitions = []
    for obj in sobjects:
        assert obj["object"]
        sobject = obj["object"]
        sobject_factory = parse_sobject_definition(sobject)
        parsed_sobject_definitions.append(sobject_factory)
    return parsed_sobject_definitions


def parse_generator(filename, copies):
    data = yaml.safe_load(open(filename, "r"))
    assert isinstance(data, list)
    return parse_sobject_list(data)