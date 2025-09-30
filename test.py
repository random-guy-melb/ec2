def filter_plan(query, spark):
    parsed = spark._jsparkSession.sessionState().sqlParser().parsePlan(query)
    plan = parsed.treeString().splitlines()
    
    keep_nodes = ("Project", "Filter", "Relation", "UnresolvedRelation", "Aggregate", "Sort", "Join")
    summary = {"tables": [], "columns": [], "filters": [], "aggregations": [], "joins": []}
    
    for line in plan:
        stripped = line.strip()
        if stripped.startswith("Project"):
            summary["columns"].append(stripped)
        elif stripped.startswith(("Filter")):
            summary["filters"].append(stripped)
        elif stripped.startswith(("Relation", "UnresolvedRelation")):
            summary["tables"].append(stripped)
        elif stripped.startswith("Aggregate"):
            summary["aggregations"].append(stripped)
        elif stripped.startswith("Join"):
            summary["joins"].append(stripped)
    
    return summary

print(filter_plan(query, spark))
