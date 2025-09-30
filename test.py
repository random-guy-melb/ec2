class LLMDataPreparer:
    def __init__(self):
        self.important_fields = [
            'error_message', 'potential_issues', 'tables', 
            'columns', 'functions', 'original_query'
        ]
    
    def prepare_for_llm(self, parse_info: Dict) -> Dict:
        """Filter and structure data for LLM consumption"""
        
        if parse_info["status"] == "error":
            return self._prepare_error_context(parse_info)
        else:
            return self._prepare_validation_context(parse_info)
    
    def _prepare_error_context(self, parse_info: Dict) -> Dict:
        """Prepare error context for LLM"""
        context = {
            "task": "fix_sql_error",
            "original_sql": parse_info["original_query"],
            "error": {
                "message": parse_info["error_message"],
                "type": parse_info.get("error_type", "unknown"),
                "potential_issues": parse_info.get("potential_issues", [])
            },
            "metadata": {
                "source": "BladeBridge conversion from Informatica",
                "target": "Spark SQL"
            }
        }
        
        # Add any successfully parsed components before the error
        if "partial_parse" in parse_info:
            context["partial_components"] = parse_info["partial_parse"]
        
        return context
    
    def _prepare_validation_context(self, parse_info: Dict) -> Dict:
        """Prepare successfully parsed SQL for validation"""
        
        # Identify potential issues even in parsed SQL
        issues = self._identify_potential_issues(parse_info)
        
        context = {
            "task": "validate_and_optimize",
            "original_sql": parse_info["original_query"],
            "components": {
                "tables": parse_info.get("tables", []),
                "columns": parse_info.get("columns", []),
                "functions": parse_info.get("functions", [])
            },
            "potential_issues": issues,
            "metadata": {
                "source": "BladeBridge conversion from Informatica",
                "target": "Spark SQL"
            }
        }
        
        return context
    
    def _identify_potential_issues(self, parse_info: Dict) -> List[str]:
        """Identify potential issues in successfully parsed SQL"""
        issues = []
        
        # Check for Informatica-specific functions that might not work
        problematic_functions = {
            'DECODE': 'Use CASE WHEN instead',
            'NVL2': 'Use CASE WHEN or COALESCE',
            'TO_DATE': 'Check date format string compatibility',
            'SYSTIMESTAMP': 'Use current_timestamp()',
            'ROWNUM': 'Use ROW_NUMBER() window function'
        }
        
        for func in parse_info.get("functions", []):
            func_name = func.get("name", "").upper()
            if func_name in problematic_functions:
                issues.append(f"{func_name}: {problematic_functions[func_name]}")
        
        return issues
