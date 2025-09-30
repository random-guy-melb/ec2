from pyspark.sql import SparkSession
import json
import re
from typing import Dict, List, Any

class SparkSQLAnalyzer:
    def __init__(self, spark):
        self.spark = spark
        self.parser = spark._jsparkSession.sessionState().sqlParser()
    
    def parse_and_extract(self, query: str) -> Dict[str, Any]:
        """Parse SQL and extract relevant information"""
        try:
            # Parse the query
            parsed = self.parser.parsePlan(query)
            
            # Extract different representations
            parse_info = {
                "status": "success",
                "original_query": query,
                "logical_plan": parsed.toString(),
                "json_plan": json.loads(parsed.prettyJson()),
                "errors": [],
                "warnings": []
            }
            
            # Extract specific components
            parse_info.update(self._extract_components(parsed))
            
        except Exception as e:
            # Capture parsing errors
            parse_info = {
                "status": "error",
                "original_query": query,
                "error_message": str(e),
                "error_type": type(e).__name__,
                "potential_issues": self._analyze_error(str(e), query)
            }
        
        return parse_info
    
    def _extract_components(self, parsed_plan) -> Dict:
        """Extract specific SQL components from parsed plan"""
        plan_str = parsed_plan.toString()
        json_plan = json.loads(parsed_plan.prettyJson())
        
        components = {
            "tables": self._extract_tables(json_plan),
            "columns": self._extract_columns(json_plan),
            "functions": self._extract_functions(json_plan),
            "joins": self._extract_joins(json_plan),
            "filters": self._extract_filters(json_plan),
            "aggregations": self._extract_aggregations(json_plan)
        }
        
        return components
    
    def _extract_tables(self, json_plan) -> List[str]:
        """Extract table references from the plan"""
        tables = []
        
        def find_tables(node):
            if isinstance(node, dict):
                if node.get("class") == "org.apache.spark.sql.catalyst.analysis.UnresolvedRelation":
                    tables.append(node.get("tableName", {}).get("name", ""))
                for value in node.values():
                    find_tables(value)
            elif isinstance(node, list):
                for item in node:
                    find_tables(item)
        
        find_tables(json_plan)
        return list(set(tables))
    
    def _extract_functions(self, json_plan) -> List[Dict]:
        """Extract function calls and their arguments"""
        functions = []
        
        def find_functions(node, path=""):
            if isinstance(node, dict):
                if "functionName" in node:
                    functions.append({
                        "name": node.get("functionName"),
                        "arguments": node.get("arguments", []),
                        "context": path
                    })
                for key, value in node.items():
                    find_functions(value, f"{path}/{key}")
            elif isinstance(node, list):
                for i, item in enumerate(node):
                    find_functions(item, f"{path}[{i}]")
        
        find_functions(json_plan)
        return functions
    
    def _extract_columns(self, json_plan) -> List[str]:
        """Extract column references"""
        columns = []
        
        def find_columns(node):
            if isinstance(node, dict):
                if node.get("class") == "org.apache.spark.sql.catalyst.analysis.UnresolvedAttribute":
                    columns.append(node.get("name", ""))
                for value in node.values():
                    find_columns(value)
            elif isinstance(node, list):
                for item in node:
                    find_columns(item)
        
        find_columns(json_plan)
        return list(set(columns))
    
    def _extract_joins(self, json_plan) -> List[Dict]:
        """Extract join information"""
        joins = []
        # Implementation specific to your needs
        return joins
    
    def _extract_filters(self, json_plan) -> List[str]:
        """Extract WHERE clause conditions"""
        filters = []
        # Implementation specific to your needs
        return filters
    
    def _extract_aggregations(self, json_plan) -> List[Dict]:
        """Extract GROUP BY and aggregate functions"""
        aggregations = []
        # Implementation specific to your needs
        return aggregations
    
    def _analyze_error(self, error_msg: str, query: str) -> List[str]:
        """Analyze error messages to identify potential issues"""
        issues = []
        
        error_patterns = {
            r"cannot resolve.*column": "Column not found - check column names and aliases",
            r"Table or view not found": "Table doesn't exist - verify table name and database",
            r"mismatched input": "Syntax error - check SQL syntax",
            r"extraneous input": "Extra characters in query",
            r"missing.*at": "Missing required SQL keyword or operator",
            r"UNION": "UNION compatibility issue - check column counts and types",
            r"data type mismatch": "Type conversion needed",
            r"aggregate.*GROUP BY": "Missing GROUP BY clause with aggregation"
        }
        
        for pattern, description in error_patterns.items():
            if re.search(pattern, error_msg, re.IGNORECASE):
                issues.append(description)
        
        return issues
