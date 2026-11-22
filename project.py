"""Check observed events against a simple tracking plan."""
import math

TITLE = "Event Contract Check"
DESCRIPTION = "Check sample analytics events against a tracking plan and locate missing or mistyped properties."
PROMPT = ("Group violations by event and property and cite example indices. "
          "Treat unobserved planned events as coverage gaps rather than implementation failures.")


def value_type(value):
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if type(value) is int:
        return "integer"
    if type(value) is float and math.isfinite(value):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise ValueError("Event payloads must contain JSON values with finite numbers.")


def analyze(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Input must be an object.")
    plan, events = data.get("plan"), data.get("events")
    if not isinstance(plan, dict) or not plan or not isinstance(events, list):
        raise ValueError("Provide a nonempty plan object and an events array.")
    allowed = {"string", "integer", "number", "boolean", "array", "object", "null"}
    for name, properties in plan.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(properties, dict):
            raise ValueError("Plan entries must map nonempty event names to property definitions.")
        for key, spec in properties.items():
            if (not isinstance(key, str) or not key.strip() or not isinstance(spec, dict)
                    or not isinstance(spec.get("type"), str) or spec["type"] not in allowed
                    or type(spec.get("required", True)) is not bool):
                raise ValueError(f"Invalid property definition for {name}.{key}.")
    rows, failed, seen = [], 0, set()
    for index, event in enumerate(events, 1):
        if (not isinstance(event, dict) or not isinstance(event.get("name"), str)
                or not event["name"].strip() or not isinstance(event.get("properties"), dict)):
            raise ValueError(f"Event {index} requires a name and a properties object.")
        name, props = event["name"], event["properties"]
        issues = []
        if name not in plan:
            issues.append(("(event)", "Unplanned event", "Defined event name", name))
        else:
            seen.add(name)
            for key, spec in plan[name].items():
                if key not in props:
                    if spec.get("required", True):
                        issues.append((key, "Missing property", spec["type"], "absent"))
                    continue
                actual = value_type(props[key])
                if actual != spec["type"] and (spec["type"], actual) != ("number", "integer"):
                    issues.append((key, "Wrong type", spec["type"], actual))
        if issues:
            failed += 1
        for prop, issue, expected, actual in issues:
            rows.append({"Sample": index, "Event": name, "Property": prop, "Finding": issue,
                         "Expected": expected, "Observed": actual})
    return {"summary": f"{failed} of {len(events)} sampled events had contract violations. "
                       f"{len(plan) - len(seen)} planned event names were absent from the sample.",
            "metrics": {"Samples": len(events), "Failing samples": failed, "Violations": len(rows),
                        "Unobserved event names": len(plan) - len(seen)}, "rows": rows}
